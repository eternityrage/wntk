import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Kate Winslet's Most Iconic Movie Roles",
        "The Timeless Talent of Kate Winslet",
        "Kate Winslet — A Hollywood Legend",
        "Best Kate Winslet Scenes of All Time",
        "From Titanic to Mare of Easttown: Kate Winslet",
        "Kate Winslet's Journey to Stardom",
        "Top 5 Kate Winslet Performances",
        "Kate Winslet Moments That Define Her Career",
        "The Grace and Power of Kate Winslet",
        "Kate Winslet Through the Years",
        "Why Kate Winslet Is One of the Greatest Actresses",
        "Behind the Scenes With Kate Winslet",
        "Kate Winslet's Oscar-Worthy Performances",
        "Rediscovering Kate Winslet's Best Films",
        "A Tribute to Kate Winslet",
    ]

    fallback_descriptions = [
        "From the bow of the Titanic to the quiet intensity of Mare of Easttown, Kate Winslet has proven time and again why she's one of the most celebrated actresses of her generation. Her performances are raw, honest, and unforgettable. This tribute celebrates the woman who brings every character to life. Drop a 🎬 if you love Kate Winslet! #katewinslet #titanic #actress #hollywood #movieclips #cinema #oscarwinner #mareofeasttown #fanpage #greatactress",
        "Kate Winslet didn't just play Rose — she became a symbol of passion, resilience, and emotional depth. Her career spans decades of extraordinary work, from period dramas to psychological thrillers. Here's a look at the roles that made her a legend. Like if you admire her craft! ✨ #katewinslet #titanic #hollywood #actress #cinema #legend #oscarwinner #movieclips #fanpage #tribute",
        "There are actors, and then there's Kate Winslet. With her fearless commitment to every role, she has delivered some of the most powerful performances in modern cinema. These are the scenes that showcase her incredible range. Comment your favorite Kate Winslet film below! 🎥 #katewinslet #movies #actress #bestscenes #cinema #hollywood #oscarwinner #fanpage #film #tribute",
        "Kate Winslet's rise to stardom is a story of talent, persistence, and authenticity. From her early roles in British cinema to becoming one of the most respected actresses in the world, she never lost her passion for the craft. This tribute honors her remarkable journey. Share this with a fellow film lover! 🌟 #katewinslet #journey #hollywood #actress #inspiration #cinema #oscarwinner #tribute #fanpage #film",
        "Whether she's breaking hearts in Titanic or solving mysteries in Mare of Easttown, Kate Winslet commands the screen with authenticity and grace. Her characters stay with you long after the credits roll. Double tap if Kate Winslet is one of your favorites! 💛 #katewinslet #titanic #mareofeasttown #actress #hollywood #cinema #movieclips #oscarwinner #fanpage #tribute",
        "Kate Winslet's red-carpet elegance is as timeless as her performances. With grace, wit, and genuine warmth, she lights up every room she enters. These moments show the woman behind the award-winning roles. Which look is your favorite? Comment below! 👗 #katewinslet #redcarpet #fashion #style #elegance #hollywood #actress #oscarwinner #glamour #fanpage",
        "A lifetime of unforgettable performances. From Sense and Sensibility to Eternal Sunshine of the Spotless Mind, Kate Winslet has given cinema some of its most moving moments. Her dedication to her craft is unmatched. Save this for your next movie night! 🍿 #katewinslet #films #actress #filmography #cinema #hollywood #oscarwinner #eternalsunshine #fanpage #tribute",
        "Behind every powerful performance is a person of incredible depth. Kate Winslet's warmth, humor, and authenticity shine through in interviews and behind-the-scenes moments. Here's a look at the real woman behind the roles. Like if you love seeing actors being their authentic selves! 🎥 #katewinslet #behindthescenes #authentic #interview #hollywood #actress #tribute #fanpage #bts #real",
        "Kate Winslet's words inspire as much as her performances. Her thoughts on acting, womanhood, and staying true to yourself resonate with fans worldwide. These are the moments where she shared her heart. Share this with someone who needs the reminder! 💬 #katewinslet #quotes #inspiration #strength #authenticity #hollywood #actress #motivation #fanpage #tribute",
        "From Oscar-winning dramas to unforgettable romances, Kate Winslet has done it all. Her versatility and emotional range set her apart as one of the greatest actresses of our time. Here's to the performances that earned her a place in cinema history. Comment your favorite role! 🏆 #katewinslet #oscarwinner #hollywood #actress #cinema #greatest #filmography #tribute #fanpage #movie",
        "What makes Kate Winslet extraordinary? Her ability to disappear completely into every character. Whether vulnerable or fierce, she brings a truth to her roles that few can match. This fan tribute celebrates her artistry. Drop a ❤️ if you're a Winslet fan! #katewinslet #acting #artistry #hollywood #actress #cinema #tribute #fanpage #movieclips #talented",
        "Some actors leave a mark on cinema forever. Kate Winslet is one of them. Her filmography is a masterclass in emotional storytelling, and her legacy continues to inspire new generations of performers. Here's a celebration of her greatest moments. Like if you agree! 🌟 #katewinslet #legacy #cinema #hollywood #actress #inspiration #filmography #tribute #fanpage #greatness",
        "There's an undeniable magic in Kate Winslet's performances. From quiet dramas to sweeping epics, she captivates audiences every single time. This is a celebration of her incredible body of work and the joy she brings to the screen. Double tap for Kate Winslet! ✨ #katewinslet #cinema #acting #talent #hollywood #movieclips #actress #tribute #fanpage #film",
        "One actress. Countless unforgettable characters. Kate Winslet has brought some of cinema's most beloved roles to life, touching hearts around the world. From Rose to Mare, she never fails to move us. Share this with a fellow Winslet fan! 🦸‍♀️ #katewinslet #titanic #mareofeasttown #actress #hollywood #cinema #iconic #oscarwinner #fanpage #tribute",
        "Kate Winslet proves that true talent never fades. Her enduring career is a testament to her dedication, her versatility, and her heart. This fan tribute is our little way of celebrating her impact on film and culture. Like if Kate Winslet inspires you! 💖 #katewinslet #hollywood #actress #cinema #legacy #inspiration #oscarwinner #tribute #fanpage #film",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "admiring and celebratory — speak as a devoted fan paying tribute",
        "cinematic and emotional — make viewers feel the power of her performances",
        "warm and appreciative — celebrate her talent, grace and authenticity",
        "inspiring and heartfelt — highlight her journey and dedication",
        "nostalgic and fond — celebrate the iconic moments fans love",
        "respectful and admiring — appreciate the craft behind the roles",
        "elegant and graceful — match the timeless quality of her work",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'WinTok Lens'. "
        f"It is a fan page dedicated to the British Hollywood actress Kate Winslet, "
        f"best known for Titanic, The Reader, Eternal Sunshine of the Spotless Mind, and Mare of Easttown. "
        f"It shares appreciation content, iconic movie moments, and tributes to her career. "
        f"It is an unofficial fan page that does not impersonate anyone - just celebrates her work. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if you love Kate Winslet! Comment your favorite Kate Winslet film below! Share this with a fellow movie lover! Follow WinTok Lens for daily Kate Winslet appreciation! "
        f"Include relevant hashtags in ALL LOWERCASE such as #katewinslet #titanic #actress #hollywood #cinema #oscarwinner #mareofeasttown #eternalsunshine #movielover #film #fanpage #appreciation #movieclips #tribute. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["katewinslet", "titanic", "actress", "hollywood", "cinema", "oscarwinner", "mareofeasttown", "eternalsunshine", "movielover", "film", "fanpage", "appreciation", "movieclips", "tribute"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
