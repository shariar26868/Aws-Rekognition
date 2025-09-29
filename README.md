# AI Lookalike & Morphing Platform

A FastAPI-based platform that uses AWS Rekognition for face recognition to find celebrity and normal person lookalikes, with advanced face morphing video generation capabilities.

## Features

- **Celebrity Lookalike Search**: Upload a photo and find matching celebrities from a curated database
- **Normal Person Lookalike Search**: Find lookalikes from a database of regular people
- **Face Morphing Videos**: Generate smooth transition videos between faces
- **AWS Integration**: Leverages AWS S3, Rekognition, and DynamoDB for scalable face recognition
- **Presigned URLs**: Secure, temporary video access through AWS S3

## Architecture

```
lookalike-platform/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── .env                            # Environment variables (not in repo)
└── backend/
    ├── config.py                   # Configuration management
    ├── services/
    │   ├── aws_service.py          # AWS operations (S3, Rekognition, DynamoDB)
    │   └── morph_service.py        # Face morphing video generation
    ├── utils/
    │   ├── image_utils.py          # Image processing utilities
    │   └── morph_utils.py          # Morphing helper functions
    ├── routers/
    │   ├── normal.py               # Normal person lookalike endpoints
    │   ├── celebrity.py            # Celebrity lookalike endpoints
    │   └── morph.py                # Morphing video endpoints
    └── video_face_transition.py    # Advanced face transition algorithms
```

## Prerequisites

- Python 3.11+
- Docker (optional)
- AWS Account with:
  - S3 buckets configured
  - Rekognition collections created
  - DynamoDB tables set up
  - IAM credentials with appropriate permissions

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lookalike-platform.git
cd lookalike-platform
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the root directory:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
MORPH_API_KEY=your_morph_api_key
NORMAL_BUCKET=your_normal_bucket
CELEBRITY_BUCKET=your_celebrity_bucket
NORMAL_COLLECTION=your_normal_collection
CELEBRITY_COLLECTION=your_celebrity_collection
NORMAL_DDB_TABLE=your_normal_table
CELEBRITY_DDB_TABLE=your_celebrity_table
```

5. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Setup

1. Build the Docker image:
```bash
docker build -t mydocker61626/simos .
```

2. Run the container:
```bash
docker run -d -p 8000:8000 --env-file .env --name lookalike-app mydocker61626/simos
```

3. View logs:
```bash
docker logs lookalike-app
```

## API Endpoints

### Root
- `GET /` - Welcome message and API information

### Celebrity Lookalike
- `POST /celebrity/add` - Upload celebrity images to the database
- `POST /celebrity/search` - Search for celebrity lookalikes

### Normal Person Lookalike
- `POST /normal/add` - Upload normal person images to the database
- `POST /normal/search` - Search for normal person lookalikes

### Morphing
- `GET /morph/video` - Generate morphing video between two faces

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Search for Celebrity Lookalike

```bash
curl -X POST "http://localhost:8000/celebrity/search" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/photo.jpg"
```

Response:
```json
{
  "matches": [
    {
      "full_name": "Celebrity Name",
      "similarity": 95.5,
      "image_key": "celebritybucket/uuid_image.jpg"
    }
  ],
  "best_match": "Celebrity Name",
  "morph_credentials": {
    "user_image_key": "temp/uuid_user.jpg",
    "celebrity_image_key": "temp/uuid_celebrity.jpg",
    "celebrity_name": "Celebrity Name"
  }
}
```

### Generate Morphing Video

```bash
curl -X GET "http://localhost:8000/morph/video?user_image_key=temp/uuid_user.jpg&celebrity_image_key=temp/uuid_celebrity.jpg"
```

Response:
```json
{
  "message": "Morph video created successfully",
  "video_key": "morph_videos/uuid.mp4",
  "video_url": "https://presigned-url..."
}
```

## Technologies Used

- **FastAPI**: Modern web framework for building APIs
- **AWS Rekognition**: Face detection and recognition
- **AWS S3**: Object storage for images and videos
- **AWS DynamoDB**: NoSQL database for face metadata
- **OpenCV**: Computer vision and video processing
- **MediaPipe**: Advanced face detection
- **NumPy**: Numerical computing
- **Pillow**: Image processing

## AWS Setup Guide

### 1. Create S3 Buckets
```bash
aws s3 mb s3://your-normal-bucket
aws s3 mb s3://your-celebrity-bucket
```

### 2. Create Rekognition Collections
```bash
aws rekognition create-collection --collection-id image_collections
aws rekognition create-collection --collection-id celebrity_images_collections
```

### 3. Create DynamoDB Tables
```bash
aws dynamodb create-table \
  --table-name facelookalike \
  --attribute-definitions AttributeName=RekognitionId,AttributeType=S \
  --key-schema AttributeName=RekognitionId,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

aws dynamodb create-table \
  --table-name celebrity-dynamo-table \
  --attribute-definitions AttributeName=RekognitionId,AttributeType=S \
  --key-schema AttributeName=RekognitionId,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

## Performance Considerations

- Face detection uses Haar Cascades for speed
- Video generation uses optimized frame processing
- Morphing creates 180 frames (6 seconds at 30 FPS)
- Temporary files are stored in S3 with cleanup recommended
- Presigned URLs expire after 1 hour by default

## Security Notes

- Never commit `.env` file or AWS credentials
- Use IAM roles with minimal required permissions
- Implement rate limiting for production use
- Set appropriate S3 bucket policies
- Enable AWS CloudTrail for audit logging

## Troubleshooting

### Docker Build Issues
If you encounter package installation errors:
```bash
# Clear Docker cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache -t mydocker61626/simos .
```

### OpenCV Issues
If face detection fails:
- Ensure proper lighting in input images
- Check that Haar Cascade files are accessible
- Verify OpenCV installation with `cv2.__version__`

### AWS Connection Issues
- Verify IAM credentials are correct
- Check AWS region configuration
- Ensure security groups allow outbound HTTPS traffic

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- AWS Rekognition for face recognition capabilities
- OpenCV community for computer vision tools
- FastAPI for the excellent web framework

## Contact

Your Name - Md.Shariar Emon Shaikat

Project Link: [[https://github.com/yourusername/lookalike-platform](https://github.com/yourusername/lookalike-platform)](https://github.com/shariar26868/Aws-Rekognition)

## Roadmap

- [ ] Add real-time face detection from webcam
- [ ] Implement batch processing for multiple images
- [ ] Add age progression/regression effects
- [ ] Support for video input (extract faces from videos)
- [ ] Add celebrity database management UI
- [ ] Implement caching for frequently accessed images
- [ ] Add support for more video formats
- [ ] Create web frontend interface
- [ ] Add user authentication and rate limiting
- [ ] Implement video quality selection options
