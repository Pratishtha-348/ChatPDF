# 💬 ChatPDF: Ask Anything About Your Documents

## 💡 Overview

**ChatPDF** is an AI-powered application that allows users to upload PDF documents and engage in a natural language conversation about their content. Think of it as having a personal research assistant that can instantly summarize, extract, and answer specific questions about large documents.

This project is built using modern ML and web technologies, providing a fast and intuitive way to interact with text data.

## 🚀 Features

* **Document Upload:** Easily upload PDF files to the application.
* **Conversational Q&A:** Ask questions about the document content in plain English.
* **Contextual Responses:** AI provides accurate answers grounded directly in the PDF text.
* **History Tracking:** Maintain the context of your conversation for a seamless experience.

## ⚙️ Installation & Setup

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.8+
* `pip` (Python package installer)
* (Optional, but recommended) A virtual environment like `venv` or `conda`.
* An API Key for your chosen LLM provider (e.g., OpenAI, Cohere, etc.).

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Pratishtha-348/ChatPDF.git](https://github.com/Pratishtha-348/ChatPDF.git)
    cd ChatPDF
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use: .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up API Key:**
    Create a file named `.env` in the root directory and add your secret key:
    ```
    OPENAI_API_KEY="your_secret_api_key_here"
    ```

5.  **Run the Application:**
    *(Note: Replace `app.py` with the name of your main entry file, e.g., `main.py` or `streamlit_app.py`)*
    ```bash
    python app.py
    ```
    The application should now be accessible in your web browser at the specified local address.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Contact
Project Link: [https://github.com/Pratishtha-348/ChatPDF](https://github.com/Pratishtha-348/ChatPDF)

