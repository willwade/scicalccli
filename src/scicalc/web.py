from flask import Flask, request, jsonify, send_file
from scicalc.calculator import Calculator
import os
import sys
import webbrowser
import signal
import logging

def setup_logging():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'calcweb.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Set up logging first
setup_logging()

# Set up Flask to find templates
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    template_dir = os.path.join(sys._MEIPASS, 'templates')
else:
    # Running from source
    # When running as a module, use the package's template directory
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')

logging.info(f"Final template directory: {template_dir}")
if not os.path.exists(template_dir):
    raise FileNotFoundError(f"Cannot find templates directory at {template_dir}")

# List contents of template directory
if os.path.exists(template_dir):
    logging.info("Template directory contents:")
    for file in os.listdir(template_dir):
        logging.info(f"  - {file}")

# Initialize Flask with explicit template and static folders
app = Flask(__name__)
app.template_folder = os.path.abspath(template_dir)  # Use absolute path
app.static_folder = os.path.abspath(template_dir)    # Use same directory for static files

# Enable Flask debug logging
logging.getLogger('flask').setLevel(logging.DEBUG)
# Add Werkzeug debug logging
logging.getLogger('werkzeug').setLevel(logging.DEBUG)

calculator = Calculator()

def signal_handler(sig, frame):
    logging.info('Shutting down calculator web server...')
    sys.exit(0)

@app.route('/')
def index():
    logging.info("Serving calculator.html")
    try:
        template_path = os.path.join(template_dir, 'calculator.html')
        logging.debug(f"Full template path: {template_path}")
        
        # Read and log the file contents
        with open(template_path, 'r') as f:
            content = f.read()
            logging.debug(f"File contents length: {len(content)}")
            logging.debug(f"First 100 chars: {content[:100]}")
        
        return send_file(template_path)
    except Exception as e:
        logging.error(f"Error serving template: {str(e)}")
        logging.exception("Full traceback:")
        return f"Error: {str(e)}", 500

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    expression = data.get('expression', '')
    try:
        result = calculator.evaluate(expression)
        return jsonify({
            'success': True,
            'result': result,
            'expression': expression
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/memory', methods=['POST'])
def memory_operation():
    data = request.get_json()
    operation = data.get('operation', '')
    
    if operation == 'MR':
        result = calculator.memory_recall()
        return jsonify({'success': True, 'result': result})
    elif operation == 'MS':
        calculator.memory_store()
        return jsonify({'success': True})
    elif operation == 'M+':
        calculator.memory_add()
        return jsonify({'success': True})
    elif operation == 'M-':
        calculator.memory_subtract()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid memory operation'})

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    port = 5000
    logging.info(f'Starting calculator web server on port {port}...')
    
    # Open browser after a short delay
    webbrowser.open(f'http://127.0.0.1:{port}', new=2)
    
    # Don't run in debug mode for production build
    debug_mode = not getattr(sys, 'frozen', False)
    
    # Run the server
    app.run(host='127.0.0.1', port=port, debug=debug_mode)

if __name__ == '__main__':
    main() 