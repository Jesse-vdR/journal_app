from app import create_app
from pyngrok import ngrok
import sys
import socket
import threading
import webbrowser
import time

def run_flask(app):
    """Run the Flask application"""
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def get_local_ip():
    """Get the local IP address"""
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

def start_ngrok():
    """Start ngrok and return the public URL"""
    try:
        # Start ngrok
        url = ngrok.connect(5000).public_url
        return url.replace('http://', 'https://')  # Force HTTPS
    except Exception as e:
        print(f"⚠️  Error starting ngrok: {str(e)}")
        print("Make sure you have ngrok installed and authenticated.")
        print("Visit https://dashboard.ngrok.com/get-started/setup for setup instructions.")
        sys.exit(1)

def main():
    # Create the Flask app
    app = create_app()
    
    # Start ngrok in a separate thread
    ngrok_url = start_ngrok()
    
    # Get local IP
    local_ip = get_local_ip()
    
    # Print URLs
    print("\n🌐 Application running at:")
    print(f"Local URL:     http://{local_ip}:5000")
    print(f"Public URL:    {ngrok_url}")
    print("\nPress Ctrl+C to quit")
    
    # Optional: Open the ngrok URL in the default browser
    print("\nOpening ngrok URL in your browser in 2 seconds...")
    threading.Timer(2, lambda: webbrowser.open(ngrok_url)).start()
    
    # Run the Flask app
    run_flask(app)

if __name__ == '__main__':
    main()
