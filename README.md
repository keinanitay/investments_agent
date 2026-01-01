# investments_agent
Data Science and Engineering final project

## Local Deployment Guide

Follow these steps to get the project running locally on your machine.

### 1. Prerequisites
*   **Python 3.11+** installed.
*   **Node.js** (v18 or higher) & **npm** installed.
*   **MongoDB**: You need a running MongoDB instance (either installed locally or a cloud URI like MongoDB Atlas).

### 2. Backend Setup (`tase-bot-backend`)

#### Option A: Local Python Environment

1.  **Navigate to the backend folder:**
    ```bash
    cd tase-bot-backend
    ```

2.  **Create and activate a virtual environment:**
    *   **Mac/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables**: Create a `.env` file inside `tase-bot-backend/` and add the following:
    ```env
    MONGO_URI=mongodb://localhost:27017  # Or your Atlas connection string
    DB_NAME=tase_bot_db
    SECRET_KEY=your_secret_key_here
    ```

5.  **Run the server:**
    ```bash
    python -m app.main
    ```
    The API will be available at `http://127.0.0.1:8000`.

#### Option B: Docker Container

If you prefer not to install Python dependencies locally, you can run the backend in a container.

1.  **Navigate to the backend folder:**
    ```bash
    cd tase-bot-backend
    ```

2.  **Create the `.env` file** as described in Option A (Step 4).
    *   *Note for Mac/Windows users:* If your MongoDB is running locally on your machine, change `MONGO_URI` to `mongodb://host.docker.internal:27017` so the container can reach your host.

3.  **Build the Docker image:**
    ```bash
    docker build -t tase-bot-backend .
    ```

4.  **Run the container:**
    ```bash
    docker run -p 8000:8000 --env-file .env tase-bot-backend
    ```

### 3. Frontend Setup (`tase-bot-ui`)

1.  Open a new terminal and navigate to the frontend folder:
    ```bash
    cd tase-bot-ui
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Run the development server:
    ```bash
    npm run dev
    ```
    The UI will be available at `http://localhost:5173`.
