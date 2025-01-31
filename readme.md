# Miro Board Export Tool

A Python utility for exporting Miro boards via official Miro REST API with automated job handling and error reporting.

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Features

- 🚀 Export multiple boards in one operation
- 📁 Save exports as ZIP files in specified directory
- 🔄 Automatic job status polling (5 minute intervals)
- ✅ Comprehensive error handling and logging
- 🔐 Secure Bearer token authentication
- 🧪 Full test coverage with pytest

## Installation
```
1. Install Python 3.13+
2. Clone the repository: git clone https://github.com/niksavis/miro-export
3. Navigate to the repository (via terminal): cd miro-export
4. Install dependencies: pip install -r requirements.txt
```

## Usage

### Basic Command
```
python miro_export.py --access-token YOUR_TOKEN --org-id YOUR_ORG_ID --board-ids "board1"
```

### Command Line Options
| Option            | Alias | Description                          | Default   |
| ----------------- | ----- | ------------------------------------ | --------- |
| `--access-token`  | `-t`  | Miro API access token (required)     |           |
| `--org-id`        | `-g`  | Organization ID (required)           |           |
| `--board-ids`     | `-b`  | Space-separated board IDs (required) |           |
| `--board-format`  | `-f`  | Export format: SVG/HTML/PDF          | SVG       |
| `--output-folder` | `-o`  | Output directory                     | ./archive |


## Error Handling

The script handles all API error responses with detailed logging:

| HTTP Code | Error Type        | Handling                    |
| --------- | ----------------- | --------------------------- |
| 400       | invalidParameters | Validate request format     |
| 401       | unauthorized      | Check access token validity |
| 403       | forbiddenAccess   | Verify permissions          |
| 404       | notFound          | Validate resource IDs       |
| 429       | tooManyRequests   | Implement retry logic       |

Example error output:
```json
{
    "status": 400,
    "code": "invalidParameters",
    "message": "Method arguments are not valid",
    "context": {
        "fields": [
            {
                "field": "request_id",
                "message": "Required UUID parameter missing",
                "reason": "missingRequiredParameter"
            }
        ]
    }
}
```

## Testing

Run the test suite with:
```
pytest test_miro_export.py -v
```

## API Requirements

- Miro Enterprise Plan
- Valid API access token with `boards:export` scope

Read the [Miro developers reference](https://developers.miro.com/reference/board-export) for more information.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create new Pull Request

## License

This repository is licensed under the [MIT License](LICENSE)

---

**[⬆ Back to Top](#miro-board-export-tool)**
