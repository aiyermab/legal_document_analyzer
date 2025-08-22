import requests
import json
import os

# API base URL
BASE_URL = "http://localhost:8000"

def test_file_path_analysis():
    """Test analyzing a document using file path"""
    url = f"{BASE_URL}/analyze/filepath"

    # Use the DOCX test file in the current workspace
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(current_dir, "test_rental_agreement.docx")

    data = {
        "file_path": test_file_path
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ File Path Analysis Successful!")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Legal Analysis:\n{result['legal_analysis']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def test_file_upload_analysis():
    """Test analyzing a document by uploading a file"""
    url = f"{BASE_URL}/analyze/file"

    # Use the DOCX test file in the current workspace
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "test_rental_agreement.docx")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': ('test_rental_agreement.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(url, files=files)

            if response.status_code == 200:
                result = response.json()
                print("✅ File Upload Analysis Successful!")
                print(f"Status: {result['status']}")
                print(f"Message: {result['message']}")
                print(f"Legal Analysis:\n{result['legal_analysis']}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")

def test_combined_endpoint_with_path():
    """Test the combined endpoint using file path"""
    url = f"{BASE_URL}/analyze/combined"

    # Use the DOCX test file in the current workspace
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(current_dir, "test_rental_agreement.docx")

    data = {
        "file_path": test_file_path
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Combined Endpoint (File Path) Analysis Successful!")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Legal Analysis:\n{result['legal_analysis']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy and running!")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running!")
        return False

if __name__ == "__main__":
    print("🧪 Testing Legal Document Analyzer API\n")

    # Check if API is running
    if check_api_health():
        print("\n" + "="*50)

        # Test file path analysis
        print("\n📁 Testing File Path Analysis:")
        test_file_path_analysis()

        print("\n" + "="*50)

        # Test combined endpoint
        print("\n🔄 Testing Combined Endpoint with File Path:")
        test_combined_endpoint_with_path()

        print("\n" + "="*50)
        print("\n💡 To test file upload, update the file_path in test_file_upload_analysis() function")
        print("💡 You can also test the API interactively at: http://localhost:8000/docs")
