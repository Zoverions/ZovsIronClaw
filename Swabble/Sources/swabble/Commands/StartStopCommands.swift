import Commander
import Foundation

@MainActor
struct StartCommand: ParsableCommand {
    static var commandDescription: CommandDescription {
        CommandDescription(commandName: "start", abstract: "Start swabble (foreground placeholder)")
    }

    mutating func run() async throws {
        let logger = Logger(level: .error)
        logger.error("Not Implemented: start command (launchd helper missing); run 'swabble serve' instead")
    }
}

@MainActor
struct StopCommand: ParsableCommand {
    static var commandDescription: CommandDescription {
        CommandDescription(commandName: "stop", abstract: "Stop swabble (placeholder)")
    }

    mutating func run() async throws {
        let logger = Logger(level: .error)
        logger.error("Not Implemented: stop command (launchd helper missing)")
    }
}

@MainActor
struct RestartCommand: ParsableCommand {
    static var commandDescription: CommandDescription {
        CommandDescription(commandName: "restart", abstract: "Restart swabble (placeholder)")
    }

    mutating func run() async throws {
        let logger = Logger(level: .error)
        logger.error("Not Implemented: restart command (launchd helper missing)")
    }
}
