import Commander
import Foundation
import Swabble

@MainActor
struct StatusCommand: ParsableCommand {
    static var commandDescription: CommandDescription {
        CommandDescription(commandName: "status", abstract: "Show daemon state")
    }

    @Option(name: .long("config"), help: "Path to config JSON") var configPath: String?

    init() {}
    init(parsed: ParsedValues) {
        self.init()
        if let cfg = parsed.options["config"]?.last { configPath = cfg }
    }

    mutating func run() async throws {
        let cfg = try? ConfigLoader.load(at: configURL)
        let wake = cfg?.wake.word ?? "clawd"
        let wakeEnabled = cfg?.wake.enabled ?? false
        let latest = await TranscriptsStore.shared.latest().suffix(3)

        // Check Neural Link Status
        let brainStatus = await checkBrainHealth()

        print("wake: \(wakeEnabled ? wake : "disabled")")
        print("brain: \(brainStatus)")

        if latest.isEmpty {
            print("transcripts: (none yet)")
        } else {
            print("last transcripts:")
            latest.forEach { print("- \($0)") }
        }
    }

    private func checkBrainHealth() async -> String {
        guard let url = URL(string: "http://localhost:8000/health") else { return "config error" }
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                return "CONNECTED (Neural Link Active)"
            }
            return "ERROR (Status: \((response as? HTTPURLResponse)?.statusCode ?? 0))"
        } catch {
            return "OFFLINE (Is GCA service running?)"
        }
    }

    private var configURL: URL? { configPath.map { URL(fileURLWithPath: $0) } }
}
