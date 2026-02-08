import Foundation

public struct HookJob: Sendable {
    public let text: String
    public let timestamp: Date

    public init(text: String, timestamp: Date) {
        self.text = text
        self.timestamp = timestamp
    }
}

public actor HookExecutor {
    private let config: SwabbleConfig
    private var lastRun: Date?
    private let hostname: String
    private let logger: Logger

    public init(config: SwabbleConfig) {
        self.config = config
        hostname = Host.current().localizedName ?? "host"
        let level = LogLevel(configValue: config.logging.level) ?? .info
        self.logger = Logger(level: level)
    }

    public func shouldRun() -> Bool {
        guard config.hook.cooldownSeconds > 0 else { return true }
        if let lastRun, Date().timeIntervalSince(lastRun) < config.hook.cooldownSeconds {
            return false
        }
        return true
    }

    public func run(job: HookJob) async throws {
        guard shouldRun() else { return }

        // Send to GCA Brain (Neural Link)
        // Fire and forget to not block the local hook
        Task {
            await sendToBrain(text: job.text)
        }

        guard !config.hook.command.isEmpty else { throw NSError(
            domain: "Hook",
            code: 1,
            userInfo: [NSLocalizedDescriptionKey: "hook command not set"]) }

        logger.info("Executing hook for: \(job.text.prefix(30))...")

        let prefix = config.hook.prefix.replacingOccurrences(of: "${hostname}", with: hostname)
        let payload = prefix + job.text

        let process = Process()
        process.executableURL = URL(fileURLWithPath: config.hook.command)
        process.arguments = config.hook.args + [payload]

        var env = ProcessInfo.processInfo.environment
        env["SWABBLE_TEXT"] = job.text
        env["SWABBLE_PREFIX"] = prefix
        for (k, v) in config.hook.env {
            env[k] = v
        }
        process.environment = env

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        try process.run()

        let timeoutNanos = UInt64(max(config.hook.timeoutSeconds, 0.1) * 1_000_000_000)
        try await withThrowingTaskGroup(of: Void.self) { group in
            group.addTask {
                process.waitUntilExit()
            }
            group.addTask {
                try await Task.sleep(nanoseconds: timeoutNanos)
                if process.isRunning {
                    process.terminate()
                }
            }
            try await group.next()
            group.cancelAll()
        }
        lastRun = Date()
    }

    private func sendToBrain(text: String) async {
        guard let url = URL(string: "http://localhost:8000/v1/observe") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "content": text,
            "modality": "audio",
            "source": "swabble",
            "timestamp": Date().timeIntervalSince1970
        ]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                logger.debug("Neural Link: Observation sent to Brain")
            } else {
                logger.warn("Neural Link: Failed to send observation (Status: \((response as? HTTPURLResponse)?.statusCode ?? 0))")
            }
        } catch {
            logger.warn("Neural Link: Connection error: \(error.localizedDescription)")
        }
    }
}
