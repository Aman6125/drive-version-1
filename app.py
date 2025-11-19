import os
from dotenv import load_dotenv
import boto3
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from io import BytesIO



# ------------------ Load Environment Variables ------------------
load_dotenv()  # reads .env file in same folder


AWS_BUCKET = os.getenv("AWS_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
print("Loaded keys:", AWS_ACCESS_KEY_ID, AWS_BUCKET)

# ------------------ Flask App Configuration ------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")

# ------------------ AWS S3 Client ------------------
s3 = boto3.client(
    "s3",
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# ------------------ Routes ------------------

@app.route("/")
def home():
    return render_template("index.html")

# Upload a file to S3
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return "❌ No file selected", 400

    filename = secure_filename(file.filename)
    try:
        s3.upload_fileobj(file, AWS_BUCKET, filename)
        return f"✅ Uploaded {filename} to {AWS_BUCKET}", 200
    except Exception as e:
        return f"❌ Upload failed: {str(e)}", 500


# List all files in S3 bucket
@app.route("/files", methods=["GET"])
def list_files():
    try:
        response = s3.list_objects_v2(Bucket=AWS_BUCKET)
        files = [obj["Key"] for obj in response.get("Contents", [])]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Download a file from S3
@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    try:
        file_stream = BytesIO()
        s3.download_fileobj(AWS_BUCKET, filename, file_stream)
        file_stream.seek(0)
        return send_file(file_stream, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"❌ Download failed: {str(e)}", 500


# ------------------ Run Flask App ------------------
if __name__ == "__main__":
    # host='0.0.0.0' allows access from other machines (e.g. EC2)
    app.run(debug=True, host="0.0.0.0", port=5000)
