import os
import urllib.request

IMAGE_URLS = {
    'hero_gym.jpg': 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1600&auto=format&fit=crop&q=80',
    'strength.jpg': 'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&auto=format&fit=crop&q=80',
    'hiit.jpg': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=800&auto=format&fit=crop&q=80',
    'cardio.jpg': 'https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=800&auto=format&fit=crop&q=80',
    'running.jpg': 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&auto=format&fit=crop&q=80',
    'cycling.jpg': 'https://images.unsplash.com/photo-1534787238916-9ba6764efd4f?w=800&auto=format&fit=crop&q=80',
    'crossfit.jpg': 'https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=800&auto=format&fit=crop&q=80',
    'yoga.jpg': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&auto=format&fit=crop&q=80',
    'pilates.jpg': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&auto=format&fit=crop&q=80',
    'squats.jpg': 'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=800&auto=format&fit=crop&q=80',
    'dumbbells.jpg': 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&auto=format&fit=crop&q=80'
}

dest_dir = os.path.join('static', 'images', 'workouts')
os.makedirs(dest_dir, exist_ok=True)

for filename, url in IMAGE_URLS.items():
    filepath = os.path.join(dest_dir, filename)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as resp, open(filepath, 'wb') as out_f:
            out_f.write(resp.read())
        print(f"Downloaded: {filename} ({os.path.getsize(filepath)} bytes)")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
