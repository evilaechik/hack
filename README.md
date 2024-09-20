
# Yandex GO Tech Support Telegram Bot

This is a Telegram bot built to provide technical support for Yandex GO services. The bot integrates with the AI21 language model for generating responses, manages an SQLite database to store frequently asked questions (FAQs), and uses the Telegram API to interact with users.

## Features

- **AI21 Integration**: Uses AI21's language generation capabilities to handle various user queries.
- **FAQ Management**: Supports FAQ storage and retrieval using an SQLite database.
- **Multi-language Support**: Designed to handle Russian-language queries (transcription and processing).
- **Feedback Collection**: Gathers user feedback via a conversational interface.
- **Tech Support**: Acts as a virtual tech support agent for Yandex GO, responding to user queries and issues.

## Prerequisites

Before running the bot, ensure you have the following:

- Python 3.x
- [Telegram Bot API Token](https://core.telegram.org/bots#botfather)
- [AI21 API Key](https://www.ai21.com/)
- [Deepgram API Key](https://developers.deepgram.com/)
- SQLite3

You can install the required Python packages using:

```bash
pip install -r requirements.txt
```

## Installation

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/your-username/yandex-go-support-bot.git
    cd yandex-go-support-bot
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up your environment variables for the Telegram Bot API, AI21 API, and Deepgram API by modifying the placeholders in the code:

    ```python
    TELEGRAM_TOKEN = '<YOUR TELEGRAM TOKEN>'
    AI21_API_KEY = '<YOUR AI21 API KEY>'
    DEEPGRAM_API_KEY = '<YOUR DEEPGRAM API KEY>'
    ```

4. Initialize the FAQ database by running the following command:

    ```bash
    python init_db.py
    ```

    This will create an `faq.db` SQLite database from the provided `faq.json` file.

## Usage

To run the bot:

```bash
python main.py
```

Once the bot is running, it can interact with users on Telegram by responding to their queries about Yandex GO, offering assistance, and collecting feedback.

### Telegram Commands

- `/start`: Start interacting with the bot.
- `/faq`: Retrieve frequently asked questions.
- `/feedback`: Provide feedback.

### Example Interaction

1. **User**: "I have an issue with Yandex GO."
2. **Bot**: "Can you describe the problem in more detail?"
3. **User**: Provides detailed issue.
4. **Bot**: Responds with potential solutions or directs the user to the FAQ.

## Database Setup

The bot uses an SQLite database (`faq.db`) to store FAQ entries. You can manage these entries by modifying the `faq.json` file and re-running the `init_db.py` script.

## Logging

The bot logs interactions and errors to help with debugging and monitoring. The logs are stored in the standard output by default but can be redirected to a file by configuring the `logging` module.

## Contributing

If you'd like to contribute to this project, please fork the repository and submit a pull request. Contributions are welcome!

## License

This project is licensed under the MIT License.
