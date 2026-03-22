default: push-streamlit

# Variables
CONNECT_SERVER ?= "your_posit_connect_server_url" # Replace with your Posit Connect server URL
QUARTO_QMD ?= "report.qmd" # Replace with your Quarto report file path
STREAMLIT_APP_DIR ?= "." # Replace with your Streamlit app directory (usually the current directory)
STREAMLIT_APP_NAME ?= "looksee" # The name to give the streamlit app
PYTHON ?= "python3" # The python interpreter to use
# Recipes

# Push the Quarto report to Posit Connect
push-quarto:
    @echo "Pushing Quarto report $(QUARTO_QMD) to Posit Connect..."
    quarto publish connect $(QUARTO_QMD) --server $(CONNECT_SERVER)

# Push the Streamlit app to Posit Connect.
# Note: This requires `rsconnect-python`. Install it using `pip install rsconnect-python`

push-streamlit:
    @echo "Deploying Streamlit app from $(STREAMLIT_APP_DIR) to Posit Connect..."
    $(PYTHON) -m rsconnect deploy app --connect-server $(CONNECT_SERVER)  --title $(STREAMLIT_APP_NAME) $(STREAMLIT_APP_DIR)

# Helper recipe to install rsconnect-python if needed
install-rsconnect:
    @echo "Installing rsconnect-python..."
    pip install rsconnect-python

.PHONY: push-quarto push-streamlit install-rsconnect
