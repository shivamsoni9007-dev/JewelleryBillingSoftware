import webview

APP_URL = "https://jewellerybillingsoftware.onrender.com"

if __name__ == "__main__":
    webview.create_window(
        "Shree Ram Kumar Jewellers",
        APP_URL,
        width=1400,
        height=900,
        min_size=(1000, 650)
    )

    webview.start()