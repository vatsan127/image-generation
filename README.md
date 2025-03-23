# Image Generation

A Flask application that converts PDF content into professional cover images using Google's Gemini AI image generation
capabilities.

## Overview

This application takes PDF files as input, extracts text from the first page, and uses Gemini AI to generate
professional course cover images with consistent layouts including title, subtitle and footer sections.

## Features

- PDF text extraction
- AI-powered image generation using Gemini
- Clean temporary file handling
- Simple web interface
- Containerized deployment

## Tech Stack

- Python 3.12
- Flask web framework
- Google Gemini AI
- Docker

## Prerequisites

- Docker installed on your system
- Google Gemini API key

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/vatsan127/image-generation.git
cd image-generation
```

2. Build the Docker image:

```bash
docker build -t image-generator .
docker run --name image-generator -p 5000:5000 -e GEMINI_API_KEY=<YOUR_API_KEY> image-generator
```

## Usage

1. Navigate to http://localhost:5000 in your browser
2. Click "Choose File" and select a PDF
3. Click "Upload" to start processing
4. Wait for the image generation to complete
5. Preview the generated image
6. Click "Download" to save the image

### For best results:
    - Use PDFs with clear, concise content
    - Ensure first page has key content
    - Keep text brief and well-formatted

## Project Structure

```
image-generator/
├── app.py # Main Flask application
├── Dockerfile # Docker configuration
├── requirements.txt # Python dependencies
├── templates/ # HTML templates
└── .gitignore # Git ignore rules
```

## Environment Variables

- Required:
  **GEMINI_API_KEY**: Your Google Gemini API key

- Optional:
  **FLASK_ENV**: Set to production by default, 
  **FLASK_APP**: Set to app.py by default
