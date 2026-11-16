
# CircuitWorks

**Version:** 0.1.0  
**Status:** Early Development  
**Course:** CS386 - Software Engineering

## About the Project

CircuitWorks is a factory automation and simulation game developed using Python and Pygame. The project aims to combine traditional factory-building gameplay with elements of electrical engineering, circuit design, and programming.

Players will be able to construct and manage their own factories, gather resources, build machines, and eventually create automated systems using programmable components.

The goal of CircuitWorks is to provide an engaging game experience while introducing concepts related to computer science, engineering, and industrial automation.

## Features

CircuitWorks is currently in early development. The project includes both implemented systems and features planned for future releases.

### Current Development
- World generation and resource nodes
- Character creation and customization
- Player and world data management
- Saving and loading functionality
- Main menu and game configuration

### Planned Features
- Factory construction and machine placement
- Resource extraction and processing
- Electrical circuit design and simulation
- Programmable controllers and automation
- More advanced inventory and crafting systems
- Expanded factory management gameplay

Features may change as development progresses.

## Technologies Used

CircuitWorks is primarily developed using:

- **Python** - Main programming language
- **Pygame** - Game rendering, input, and event handling
- **SymPy** - Mathematical functionality
- **JSON** - Data storage and configuration
- **Git/GitHub** - Version control and collaboration

## Installation

### Prerequisites

Before running CircuitWorks, make sure you have the following installed:

- Python 3.10 or newer
- Git
- pip (Python package manager)

### 1. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/Brown-Raccoon/CircuitWorks.git
```

Navigate to the project directory:

```bash
cd CircuitWorks
```

### 2. Install Dependencies

Install the required Python libraries:

```bash
python -m pip install pygame sympy
```

Additional dependencies may be required as the project develops.

### 3. Run CircuitWorks

To launch the application, run:

```bash
python "main menu.py"
```

**Note:** CircuitWorks is still under development. Some features may be incomplete, and the current version may require additional project modules or configuration before running successfully.

## Usage

CircuitWorks is designed around building and managing an automated factory.

The intended gameplay involves:

1. Starting or loading a game world.
2. Exploring the world and locating resources.
3. Gathering materials for construction.
4. Placing machines and constructing factory systems.
5. Connecting machines through electrical circuits.
6. Programming and managing automated production processes.

Not all gameplay features are available in the current development version.

## Project Structure

The repository contains several Python modules responsible for different parts of the game.

Some important components include:

| File | Description |
|------|-------------|
| `main menu.py` | Main menu and application entry point |
| `world_generation.py` | World generation functionality |
| `world_generation_settings.py` | World generation configuration |
| `character.py` | Character-related functionality |
| `character_creator.py` | Character creation system |
| `save_handler.py` | Saving and loading game data |

The project structure may change as development continues.

## Versioning

CircuitWorks follows [Semantic Versioning](https://semver.org/).

The current version is **0.1.0**.

Version numbers use the following format:

`MAJOR.MINOR.PATCH`

- **MAJOR:** Significant changes that may introduce incompatibilities.
- **MINOR:** New features and functionality.
- **PATCH:** Bug fixes and minor improvements.

Because CircuitWorks is still in its initial development phase, its version number begins with `0`.

The corresponding Git release tag is intended to be `v0.1.0`.

## Contributing

CircuitWorks is a collaborative software engineering project, and contributions that improve the project are welcome.

To contribute:

1. Fork the repository or create a new development branch.
2. Make your changes in that branch.
3. Follow the project's existing Python coding conventions.
4. Test your changes before submitting them.
5. Commit your changes with a meaningful commit message.
6. Push your branch to GitHub.
7. Open a pull request targeting the `main` branch.

Pull requests should include a short description of the changes and any relevant testing information.

Contributors are encouraged to discuss major changes with the development team before implementation.

## License

CircuitWorks is proposed to be licensed under the **MIT License**.

The MIT License was selected because it provides a straightforward and permissive framework for open-source software development. It allows others to use, modify, and distribute the source code while requiring preservation of the original copyright and license notice.

This makes it suitable for CircuitWorks as a collaborative educational project, encouraging future development and contributions.

See the [LICENSE](LICENSE) file for the complete license terms once the license has been approved and added to the repository.

## Project Repository

GitHub: https://github.com/Brown-Raccoon/CircuitWorks
