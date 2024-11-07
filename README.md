# EzCommit

## Overview

EzCommit is a tool designed to simplify the process of managing Git repositories, particularly focusing on commit management and pull request generation. The tool leverages AI to assist with generating commit messages and summarizing pull requests.

## Description

EzCommit provides a user-friendly interface to streamline the process of creating commits and pull requests. It uses AI to generate meaningful commit messages and summaries, making it easier to manage and understand changes in your codebase. The tool supports various configurations and integrates with external APIs for enhanced functionality.

## Getting Started

### Dependencies

To run EzCommit, you need to have the following dependencies installed:

- Python 3.x
- Git
- Mistral API (for AI-generated commit messages)

You can find the list of Python packages required in the `requirements.txt` file.

### Installing

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/ezcommit.git
   cd ezcommit
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Executing the Program

To run EzCommit, use the following command:
```bash
ezcommit --help
```

For more specific commands, you can refer to the help menu by running:
```bash
ezcommit --help
```

### Configuration

1. **Initialize Configuration:**
   ```bash
   ezcommit --init
   ```

2. **Set API Key:**
   ```bash
   ezcommit --api-key
   ```

3. **Set Convention Path:**
   ```bash
   ezcommit --convention-path
   ```

4. **Set Context Path:**
   ```bash
   ezcommit --context-path
   ```

5. **Reinitialize Configuration:**
   ```bash
   ezcommit --reinit
   ```

6. **Remove Configuration:**
   ```bash
   ezcommit --remove
   ```

### Common Commands

- **Generate Commit:**
  ```bash
  ezcommit --gen-cmt
  ```

- **Visualize Commit History:**
  ```bash
  ezcommit --visual
  ```

- **Summarize Pull Requests:**
  ```bash
  ezcommit --sum
  ```

- **Create Pull Request:**
  ```bash
  ezcommit --gen-pr
  ```

- **Create README:**
  ```bash
  ezcommit --readme
  ```

## Help

For common problems, refer to the help menu by running:
```bash
ezcommit --help
```

## Version History

### 0.1.4
- Various bug fixes and optimizations.
- See [commit change]() or [release history]().

### 0.1
- Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details.
