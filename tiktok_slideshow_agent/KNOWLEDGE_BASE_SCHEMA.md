# Knowledge Base Schema

The core of the agent's memory is `slideshows.json`. This file acts as a comprehensive log of every generated slideshow, capturing the exact text and image used for every single slide.

## 1. Slideshow Log (`slideshows.json`)

This file contains an array of slideshow objects. It consolidates all projects and runs into a single structure.

```json
[
  {
    "id": "uuid-1234-5678",
    "project_id": "motivation_daily",
    "topic": "Discipline",
    "created_at": "2025-12-26T10:00:00Z",
    "slide_count": 5,
    "slides": [
      {
        "slide_number": 1,
        "type": "hook",
        "text": "Why you will regret not starting today",
        "image_path": "/Users/mindreader/images/dark_aesthetic/img_01.jpg",
        "visual_notes": "High contrast text, dark background"
      },
      {
        "slide_number": 2,
        "type": "content",
        "text": "The pain of discipline weighs ounces.",
        "image_path": "/Users/mindreader/images/dark_aesthetic/img_02.jpg"
      },
      {
        "slide_number": 3,
        "type": "content",
        "text": "The pain of regret weighs tons.",
        "image_path": "/Users/mindreader/images/dark_aesthetic/img_03.jpg"
      },
      {
        "slide_number": 4,
        "type": "content",
        "text": "Choose your pain wisely.",
        "image_path": "/Users/mindreader/images/dark_aesthetic/img_04.jpg"
      },
      {
        "slide_number": 5,
        "type": "cta",
        "text": "Follow for daily motivation.",
        "image_path": "/Users/mindreader/images/dark_aesthetic/img_05.jpg"
      }
    ],
    "drive_folder_link": "https://drive.google.com/drive/folders/..."
  }
]
```

## 2. Future Extensions
- **`hooks.json`**: Can be derived from `slideshows.json` by filtering for `slide_number: 1`.
- **`performance.json`**: Can link to `id` in `slideshows.json` to add view counts/likes later.
