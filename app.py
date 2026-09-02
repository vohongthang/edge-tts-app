"""
Hệ Thống Chuyển Văn Bản Thành Giọng Nói AI (Edge-TTS)
------------------------------------------------------
Ứng dụng Streamlit tạo giọng đọc AI tự động đa chủ đề, sử dụng thư viện
`edge-tts` (Microsoft Edge Text-to-Speech) - MIỄN PHÍ 100%, KHÔNG CẦN API KEY.

Chạy ứng dụng:
    streamlit run app.py
"""

import asyncio
import io
import re
from datetime import datetime

import edge_tts
import requests
import streamlit as st
from pydub import AudioSegment

# =====================================================================================
# 1. CẤU HÌNH TRANG (PAGE CONFIG)
# =====================================================================================
st.set_page_config(
    page_title="Trình Tạo Giọng Đọc AI Đa Chủ Đề",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================================
# 1b. GIAO DIỆN THƯƠNG HIỆU THẮNG VÕ + TỐI ƯU ĐIỆN THOẠI
# =====================================================================================
st.markdown(
    """
    <style>
    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button {
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 3px 10px rgba(211, 47, 47, 0.35);
        transition: transform 0.12s ease;
    }
    div[data-testid="stButton"] button:active,
    div[data-testid="stDownloadButton"] button:active { transform: scale(0.98); }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stDownloadButton"] button:hover {
        border: 1px solid #FFC107;
        color: #FFC107;
    }
    .brand-signature {
        text-align: right;
        font-family: cursive;
        color: #FFC107;
        font-size: 0.95rem;
        padding-bottom: 4px;
    }
    h2, h3 { border-left: 4px solid #D32F2F; padding-left: 10px; }
    @media (max-width: 640px) {
        .block-container { padding-left: 0.8rem; padding-right: 0.8rem; padding-top: 1rem; }
        textarea, input, select { font-size: 1rem !important; }
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button {
            width: 100%;
            padding: 0.85rem 1rem;
            font-size: 1.05rem;
        }
        h1 { font-size: 1.5rem !important; }
        h2, h3 { font-size: 1.15rem !important; }
    }
    </style>
    <div class="brand-signature">✍️ Thắng Võ</div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================================
# 2. DANH MỤC GIỌNG ĐỌC (VOICE DICT)
# =====================================================================================
VOICES = {
    "🇻🇳 Nam Minh - Nam (Miền Bắc)": {
        "id": "vi-VN-NamMinhNeural",
        "desc": "Giọng nam miền Bắc, trầm ấm, chuẩn mực. Phù hợp: Bản tin, Bất động sản, Doanh nghiệp.",
    },
    "🇻🇳 Hoài My - Nữ (Miền Bắc)": {
        "id": "vi-VN-HoaiMyNeural",
        "desc": "Giọng nữ miền Bắc, truyền cảm, nhẹ nhàng. Phù hợp: Phóng sự, Review, Storytelling.",
    },
    "🇺🇸 Jenny - Nữ, thân thiện": {
        "id": "en-US-JennyNeural",
        "desc": "Giọng nữ tiếng Anh Mỹ chuẩn, tự nhiên, thân thiện. Phù hợp: Nội dung chung, E-learning.",
    },
    "🇺🇸 Guy - Nam, mạnh mẽ": {
        "id": "en-US-GuyNeural",
        "desc": "Giọng nam tiếng Anh Mỹ, rõ ràng, mạnh mẽ. Phù hợp: Thuyết trình, Quảng cáo.",
    },
    "🇺🇸 Aria - Nữ, ấm áp đa năng": {
        "id": "en-US-AriaNeural",
        "desc": "Giọng nữ tiếng Anh Mỹ ấm áp, biểu cảm tự nhiên. Phù hợp: Review, Storytelling, Quảng cáo.",
    },
    "🇺🇸 Christopher - Nam, trầm ổn trọng": {
        "id": "en-US-ChristopherNeural",
        "desc": "Giọng nam trầm, uy tín, đáng tin cậy. Phù hợp: Tin tức, Doanh nghiệp, Giáo dục.",
    },
    "🇺🇸 Eric - Nam, điềm đạm rõ ràng": {
        "id": "en-US-EricNeural",
        "desc": "Giọng nam điềm đạm, phát âm rõ ràng. Phù hợp: E-learning, Hướng dẫn, Tutorial.",
    },
    "🇺🇸 Michelle - Nữ, chuyên nghiệp": {
        "id": "en-US-MichelleNeural",
        "desc": "Giọng nữ chuyên nghiệp, sắc sảo. Phù hợp: Doanh nghiệp, Thuyết trình, Tin tức.",
    },
    "🇺🇸 Roger - Nam, ấm áp từng trải": {
        "id": "en-US-RogerNeural",
        "desc": "Giọng nam lớn tuổi hơn, ấm áp, từng trải. Phù hợp: Kể chuyện, Audiobook, Podcast.",
    },
    "🇺🇸 Ana - Nữ, giọng trẻ em": {
        "id": "en-US-AnaNeural",
        "desc": "Giọng bé gái trong trẻo. Phù hợp: Nội dung thiếu nhi, Giáo dục mầm non.",
    },
    "🇺🇸 Andrew (Multilingual) - Nam, tự nhiên": {
        "id": "en-US-AndrewMultilingualNeural",
        "desc": "Giọng nam đa ngôn ngữ, tự nhiên như hội thoại đời thực. Phù hợp: Podcast, MC sự kiện, Kể chuyện.",
    },
    "🇺🇸 Ava (Multilingual) - Nữ, biểu cảm": {
        "id": "en-US-AvaMultilingualNeural",
        "desc": "Giọng nữ đa ngôn ngữ, biểu cảm sống động. Phù hợp: Quảng cáo, Review, Nội dung sáng tạo.",
    },
    "🇬🇧 Sonia - Nữ, thanh lịch Anh-Anh": {
        "id": "en-GB-SoniaNeural",
        "desc": "Giọng nữ Anh-Anh thanh lịch, sang trọng. Phù hợp: Bất động sản cao cấp, Quảng cáo premium.",
    },
    "🇬🇧 Ryan - Nam, lịch lãm Anh-Anh": {
        "id": "en-GB-RyanNeural",
        "desc": "Giọng nam Anh-Anh lịch lãm, chững chạc. Phù hợp: Doanh nghiệp, MC sự kiện, Quảng cáo premium.",
    },
}

VN_VOICE_KEYS = [k for k in VOICES if k.startswith("🇻🇳")]
FOREIGN_VOICE_KEYS = [k for k in VOICES if not k.startswith("🇻🇳")]

# =====================================================================================
# 3. KHO KỊCH BẢN MẪU THEO CHỦ ĐỀ x VÙNG MIỀN (TEMPLATES SELECTOR)
# =====================================================================================
TOPIC_OPTIONS = [
    "🏢 Bất Động Sản (Sang trọng / Thôi thúc)",
    "📰 Tin Tức / Phóng Sự",
    "📖 Review / Kể Chuyện",
    "📢 Quảng Cáo / Giới Thiệu Sản Phẩm",
    "🎓 Giáo Dục / E-Learning",
    "🎧 Podcast / Truyện Audio",
    "💍 MC Sự Kiện / Đám Cưới",
    "✍️ Tự nhập văn bản tự do",
]

REGIONS = {
    "Nghệ An (TP Vinh)": {"noun_phrase": "thành phố Vinh, xứ Nghệ", "landmark": "sông Lam"},
    "Huế (Cố đô)": {"noun_phrase": "cố đô Huế nghìn năm văn hiến", "landmark": "sông Hương"},
    "Đà Nẵng": {"noun_phrase": "thành phố đáng sống Đà Nẵng", "landmark": "sông Hàn"},
    "Hà Nội": {"noun_phrase": "thủ đô Hà Nội ngàn năm văn hiến", "landmark": "sông Hồng"},
    "TP. Hồ Chí Minh": {"noun_phrase": "thành phố Hồ Chí Minh năng động", "landmark": "sông Sài Gòn"},
}

CURATED_SCRIPTS = {}


def _build_generic_script(topic_label: str, region_label: str) -> str:
    info = REGIONS[region_label]
    city = info["noun_phrase"]
    river = info["landmark"]

    if topic_label.startswith("🏢"):
        return (
            f"Tọa lạc bên dòng {river} thơ mộng, ngay giữa lòng {city}, dự án khu đô thị mới "
            f"tự hào mang đến một chuẩn sống thượng lưu chưa từng có tại khu vực.\n\n"
            f"Không chỉ là nơi an cư, đây còn là biểu tượng phồn vinh mới - nơi hội tụ trọn vẹn hệ "
            f"sinh thái tiện ích đẳng cấp quốc tế.\n\n"
            f"Cơ hội sở hữu bất động sản ven {river} đang đến rất gần. Quý khách hàng vui lòng liên hệ "
            f"ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư "
            f"vấn và giữ chỗ sớm nhất."
        )
    if topic_label.startswith("📰"):
        return (
            f"Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi "
            f"bật về tốc độ phát triển hạ tầng tại {city}.\n\n"
            f"Trong những năm gần đây, khu vực này đang chuyển mình mạnh mẽ để trở thành một trong "
            f"những trung tâm kinh tế, văn hóa quan trọng của cả nước.\n\n"
            f"Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý "
            f"vị trong những bản tin tiếp theo."
        )
    if topic_label.startswith("📖"):
        return (
            f"Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven {river}, và cảm giác đầu tiên khi "
            f"bước chân xuống xe là một sự bình yên đến lạ.\n\n"
            f"Gió từ sông thổi vào mát rượi, không gian sống nơi đây thực sự khác biệt so với sự ồn "
            f"ào, ngột ngạt của phố thị mà tôi vẫn quen thuộc mỗi ngày.\n\n"
            f"Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị "
            f"ven {river} này tại {city} rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
        )
    if topic_label.startswith("📢"):
        return (
            f"Bạn đang tìm kiếm một sản phẩm chất lượng, được hàng ngàn khách hàng tin dùng tại "
            f"{city}? Xin giới thiệu đến quý khách bộ sản phẩm mới nhất, được nghiên cứu và phát "
            f"triển dành riêng cho người tiêu dùng tại khu vực.\n\n"
            f"Nhân dịp khai trương chi nhánh mới tại {city}, chúng tôi dành tặng ưu đãi giảm giá đặc "
            f"biệt lên đến ba mươi phần trăm cho một trăm khách hàng đặt mua sớm nhất.\n\n"
            f"Đừng bỏ lỡ cơ hội này! Quý khách vui lòng liên hệ ngay hotline, hoặc Zalo không không "
            f"chín bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn miễn phí và nhận ưu đãi ngay hôm nay."
        )
    if topic_label.startswith("🎓"):
        return (
            f"Chào mừng các bạn học viên đã đến với bài học hôm nay, được thực hiện bởi đội ngũ "
            f"giảng viên giàu kinh nghiệm tại trung tâm đào tạo {city}.\n\n"
            f"Trong bài học này, chúng ta sẽ cùng nhau tìm hiểu những kiến thức nền tảng quan trọng.\n\n"
            f"Bây giờ, chúng ta hãy cùng bắt đầu bài học đầu tiên nhé!"
        )
    if topic_label.startswith("🎧"):
        return (
            f"Xin chào tất cả các bạn, chào mừng các bạn đã quay trở lại với podcast của chúng tôi, "
            f"nơi mỗi tuần chúng ta cùng nhau trò chuyện về những câu chuyện đời thường thật gần gũi.\n\n"
            f"Số phát sóng hôm nay, mình muốn kể cho các bạn nghe về một buổi chiều lang thang dọc "
            f"{river}, {city} - nơi mình tình cờ gặp gỡ những con người bình dị nhưng mang trong "
            f"mình biết bao câu chuyện thú vị.\n\n"
            f"Cảm ơn các bạn đã lắng nghe, hẹn gặp lại trong số phát sóng tuần sau!"
        )
    return (
        f"Kính thưa quý vị quan khách, cô dâu chú rể cùng toàn thể gia đình hai họ! Trong không khí "
        f"ấm áp và hạnh phúc tại {city} hôm nay, chúng ta cùng nhau hội tụ để chứng kiến khoảnh khắc "
        f"thiêng liêng - lễ thành hôn của đôi uyên ương.\n\n"
        f"Xin chúc cô dâu chú rể trăm năm hạnh phúc, bạc đầu răng long, sớm sinh quý tử!"
    )


def get_script_text(topic_label: str, region_label: str) -> str:
    if topic_label == "✍️ Tự nhập văn bản tự do":
        return ""
    key = (topic_label, region_label)
    if key in CURATED_SCRIPTS:
        return CURATED_SCRIPTS[key]
    return _build_generic_script(topic_label, region_label)


# =====================================================================================
# 3b. THẺ CẢM XÚC & KỊCH BẢN MẪU CHO CHẾ ĐỘ HỘI THOẠI
# =====================================================================================
EMOTION_TAGS = {
    "vui": {"rate": 10, "pitch": 5, "volume": 0, "label": "😄 Vui vẻ"},
    "hào hứng": {"rate": 16, "pitch": 8, "volume": 8, "label": "🤩 Hào hứng / phấn khích"},
    "buồn": {"rate": -14, "pitch": -6, "volume": -6, "label": "😢 Buồn / trầm lắng"},
    "nghẹn ngào": {"rate": -18, "pitch": -8, "volume": -8, "label": "🥲 Nghẹn ngào, xúc động"},
    "giận": {"rate": 10, "pitch": 3, "volume": 14, "label": "😠 Giận dữ, gắt gỏng"},
    "ngạc nhiên": {"rate": 6, "pitch": 12, "volume": 6, "label": "😲 Ngạc nhiên"},
    "thì thầm": {"rate": -10, "pitch": -3, "volume": -35, "label": "🤫 Thì thầm, nhỏ nhẹ"},
    "trang trọng": {"rate": -6, "pitch": -2, "volume": 0, "label": "🎩 Trang trọng, nghiêm túc"},
    "cười": {"rate": 14, "pitch": 10, "volume": 6, "label": "😂 Cười / vui đùa"},
    "khóc": {"rate": -20, "pitch": -8, "volume": -10, "label": "😭 Khóc / nức nở"},
}
AUTO_FX_TAGS = {"cười", "khóc"}
AUTO_FX_PHRASES = {
    "cười": "Ha ha ha ha!",
    "khóc": "Hức... hức... hức...",
}

_EMOTION_TAG_SPLIT_RE = re.compile(r"\[([^\[\]]+)\]")

DIALOGUE_TOPIC_OPTIONS = [
    "📖 Kể Chuyện Cảm Xúc (vui - buồn - bất ngờ)",
    "😂 Hài Hước / Tấu Hài",
    "🏢 Tư Vấn Bất Động Sản",
    "🎙️ Phỏng Vấn Podcast",
    "✍️ Tự soạn kịch bản",
]


def _dialogue_names(speaker_names: list) -> list:
    names = [n for n in speaker_names if n]
    while len(names) < 3:
        names.append(names[-1] if names else "Người nói")
    return names


def build_dialogue_template(topic_label: str, speaker_names: list) -> str:
    if topic_label == "✍️ Tự soạn kịch bản" or not speaker_names:
        return ""

    n = len(speaker_names)
    a, b, c = _dialogue_names(speaker_names)

    if topic_label == "📖 Kể Chuyện Cảm Xúc (vui - buồn - bất ngờ)":
        script = (
            f"{a}: [vui] Cậu biết không, hồi nhỏ tớ hay ra bờ sông ngồi câu cá với ông tớ vào "
            f"mỗi buổi chiều, vui lắm!\n"
            f"{b}: [ngạc nhiên] Ồ thật á? Nghe hay quá, kể tiếp đi!\n"
            f"{a}: Ông hay kể chuyện ngày xưa, rồi hai ông cháu cứ thế mà cười suốt. [cười]\n"
            f"{b}: [buồn] Nhưng mà... [nghẹn ngào] năm ngoái ông mất rồi, chắc cậu nhớ ông lắm.\n"
        )
        if n >= 3:
            script += (
                f"{c}: [thì thầm] Ông chắc đang ở trên đó nhìn cậu cười vui mỗi ngày đó.\n"
                f"{a}: [vui] Cảm ơn cậu, nghe vậy tớ thấy ấm lòng ghê. [cười]\n"
            )
        return script

    if topic_label == "😂 Hài Hước / Tấu Hài":
        script = (
            f"{a}: [vui] Này, đố cậu biết vì sao con gà lại băng qua đường?\n"
            f"{b}: [ngạc nhiên] Ơ, sao vậy ta?\n"
            f"{a}: Vì nó muốn xem thử bên kia đường có ngon hơn không thôi! [cười]\n"
            f"{b}: Trời ơi, nhạt như nước ốc mà sao tớ vẫn buồn cười! [cười]\n"
        )
        if n >= 3:
            script += (
                f"{c}: [giận] Hai người thôi giỡn nữa được không, tới giờ họp rồi kìa!\n"
                f"{a}: [thì thầm] Suỵt, để tớ kể nốt câu cuối đã...\n"
            )
        return script

    if topic_label == "🏢 Tư Vấn Bất Động Sản":
        script = (
            f"{a}: [trang trọng] Chào anh chị, em là {a}, tư vấn viên dự án khu đô thị ven sông "
            f"hôm nay ạ.\n"
            f"{b}: [vui] Chào em, vợ chồng anh chị đang quan tâm căn góc view sông đó.\n"
            f"{a}: Dạ vâng, căn đó view cực đẹp, [hào hứng] đang có ưu đãi chiết khấu tám phần "
            f"trăm cho khách đặt cọc sớm ạ!\n"
            f"{b}: [ngạc nhiên] Ưu đãi tốt vậy à? Vậy chính sách thanh toán thế nào em?\n"
        )
        if n >= 3:
            script += (
                f"{c}: [thì thầm] Anh ơi, em thấy giá này hợp lý đó, mình chốt luôn đi.\n"
                f"{a}: [vui] Dạ, để em gửi anh chị bảng giá chi tiết qua Zalo ạ.\n"
            )
        return script

    script = (
        f"{a}: [trang trọng] Xin chào mọi người đã quay lại với podcast của tụi mình, hôm nay "
        f"có khách mời đặc biệt là {b}.\n"
        f"{b}: [vui] Chào mọi người, rất vui được ở đây hôm nay!\n"
        f"{a}: Vậy điều gì đã truyền cảm hứng để bạn bắt đầu công việc này?\n"
        f"{b}: [hào hứng] Ồ, đó là một câu chuyện dài, [cười] nhưng để tớ kể ngắn gọn thôi...\n"
    )
    if n >= 3:
        script += (
            f"{c}: [ngạc nhiên] Chờ đã, cho tớ hỏi xen một câu được không?\n"
            f"{a}: [vui] Được chứ, cứ hỏi thoải mái!\n"
        )
    return script


# =====================================================================================
# 4. XỬ LÝ BẤT ĐỒNG BỘ - GỌI EDGE-TTS
# =====================================================================================
async def _synthesize_speech(text: str, voice_id: str, rate: str, pitch: str, volume: str = "+0%") -> bytes:
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate, pitch=pitch, volume=volume)
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    return audio_buffer.getvalue()


def run_async_task(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def generate_voice(text: str, voice_id: str, rate_value: int, pitch_value: int, volume_value: int = 0) -> bytes:
    rate_str = f"{rate_value:+d}%"
    pitch_str = f"{pitch_value:+d}Hz"
    volume_str = f"{volume_value:+d}%"
    return run_async_task(_synthesize_speech(text, voice_id, rate_str, pitch_str, volume_str))


# =====================================================================================
# 4b. CHẾ ĐỘ HỘI THOẠI NHIỀU GIỌNG (2-3 NGƯỜI NÓI CHUYỆN)
# =====================================================================================
def _split_emotion_segments(text: str) -> list:
    parts = _EMOTION_TAG_SPLIT_RE.split(text)
    segments = []
    current_emotion = None

    first = parts[0].strip()
    if first:
        segments.append({"emotion": None, "text": first, "auto_fx": False})

    i = 1
    while i < len(parts):
        tag_raw = parts[i].strip().lower()
        following = parts[i + 1] if i + 1 < len(parts) else ""
        if tag_raw in EMOTION_TAGS:
            current_emotion = tag_raw
        following_stripped = following.strip()
        if following_stripped:
            segments.append({"emotion": current_emotion, "text": following_stripped, "auto_fx": False})
        elif current_emotion in AUTO_FX_TAGS:
            segments.append({"emotion": current_emotion, "text": "", "auto_fx": True})
        i += 2

    return segments


def parse_dialogue_script(script: str, speaker_names: list) -> list:
    name_lookup = {name.strip().lower(): name for name in speaker_names if name.strip()}
    turns = []
    current_speaker = None
    current_lines = []

    def flush():
        if current_speaker is not None:
            text = " ".join(line for line in current_lines if line).strip()
            if text:
                segments = _split_emotion_segments(text)
                if segments:
                    turns.append((current_speaker, segments))

    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = False
        if ":" in line:
            prefix, rest = line.split(":", 1)
            key = prefix.strip().lower()
            if key in name_lookup:
                flush()
                current_speaker = name_lookup[key]
                current_lines = [rest.strip()]
                matched = True
        if not matched:
            if current_speaker is None:
                continue
            current_lines.append(line)

    flush()
    return turns


def generate_dialogue_audio(
    turns: list,
    speaker_voice_map: dict,
    speaker_pitch_map: dict,
    rate_value: int,
    base_pitch_value: int,
    pause_ms: int = 450,
    segment_gap_ms: int = 120,
) -> bytes:
    combined = AudioSegment.silent(duration=0)

    for speaker, segments in turns:
        voice_id = speaker_voice_map[speaker]
        speaker_pitch_offset = speaker_pitch_map.get(speaker, 0)

        for seg in segments:
            emotion_cfg = EMOTION_TAGS.get(seg["emotion"], {}) if seg["emotion"] else {}
            text_to_speak = AUTO_FX_PHRASES.get(seg["emotion"], "") if seg["auto_fx"] else seg["text"]
            if not text_to_speak.strip():
                continue

            seg_rate = max(-50, min(50, rate_value + emotion_cfg.get("rate", 0)))
            seg_pitch = max(-50, min(50, base_pitch_value + speaker_pitch_offset + emotion_cfg.get("pitch", 0)))
            seg_volume = max(-50, min(50, emotion_cfg.get("volume", 0)))

            segment_bytes = generate_voice(text_to_speak, voice_id, seg_rate, seg_pitch, seg_volume)
            segment_audio = AudioSegment.from_file(io.BytesIO(segment_bytes), format="mp3")
            combined += segment_audio + AudioSegment.silent(duration=segment_gap_ms)

        combined += AudioSegment.silent(duration=pause_ms)

    buffer = io.BytesIO()
    combined.export(buffer, format="mp3", bitrate="128k")
    return buffer.getvalue()


# =====================================================================================
# 4c. ELEVENLABS (ENGINE CAO CẤP: CẢM XÚC THẬT, GIỌNG ADAM)
# =====================================================================================
ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVEN_VOICES_URL = "https://api.elevenlabs.io/v1/voices"


@st.cache_data(show_spinner=False, ttl=300)
def eleven_list_voices(api_key: str):
    headers = {"xi-api-key": api_key}
    r = requests.get(ELEVEN_VOICES_URL, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    return [(v["name"], v["voice_id"]) for v in data.get("voices", [])]


def eleven_tts_speak(text: str, voice_id: str, api_key: str, model_id: str = "eleven_v3",
                      stability: float = 0.5, similarity: float = 0.8) -> bytes:
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": stability, "similarity_boost": similarity},
    }
    r = requests.post(ELEVEN_TTS_URL.format(voice_id=voice_id), headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs lỗi {r.status_code}: {r.text[:300]}")
    return r.content


def parse_dialogue_script_raw(script: str, speaker_names: list) -> list:
    name_lookup = {name.strip().lower(): name for name in speaker_names if name.strip()}
    turns = []
    current_speaker = None
    current_lines = []

    def flush():
        if current_speaker is not None:
            text = " ".join(line for line in current_lines if line).strip()
            if text:
                turns.append((current_speaker, text))

    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        matched = False
        if ":" in line:
            prefix, rest = line.split(":", 1)
            key = prefix.strip().lower()
            if key in name_lookup:
                flush()
                current_speaker = name_lookup[key]
                current_lines = [rest.strip()]
                matched = True
        if not matched:
            if current_speaker is None:
                continue
            current_lines.append(line)

    flush()
    return turns


def eleven_generate_dialogue_audio(turns_raw: list, speaker_voice_map: dict, api_key: str,
                                    model_id: str = "eleven_v3", pause_ms: int = 450) -> bytes:
    combined = AudioSegment.silent(duration=0)
    for speaker, text in turns_raw:
        voice_id = speaker_voice_map.get(speaker)
        if not voice_id:
            continue
        clip_bytes = eleven_tts_speak(text, voice_id, api_key, model_id)
        combined += AudioSegment.from_file(io.BytesIO(clip_bytes), format="mp3")
        combined += AudioSegment.silent(duration=pause_ms)
    buffer = io.BytesIO()
    combined.export(buffer, format="mp3", bitrate="128k")
    return buffer.getvalue()


# =====================================================================================
# 5. KHỞI TẠO SESSION STATE
# =====================================================================================
DEFAULT_TOPIC_KEY = "🏢 Bất Động Sản (Sang trọng / Thôi thúc)"
DEFAULT_REGION_KEY = "Nghệ An (TP Vinh)"

if "script_text" not in st.session_state:
    st.session_state.script_text = get_script_text(DEFAULT_TOPIC_KEY, DEFAULT_REGION_KEY)

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "last_voice_label" not in st.session_state:
    st.session_state.last_voice_label = None


def _apply_template():
    topic_choice = st.session_state.template_choice
    region_choice = st.session_state.get("region_choice", DEFAULT_REGION_KEY)
    st.session_state.script_text = get_script_text(topic_choice, region_choice)
    st.session_state.audio_bytes = None


def _on_toggle_foreign_voices():
    if not st.session_state.get("show_foreign_voices", False):
        if st.session_state.get("voice_choice") not in VN_VOICE_KEYS:
            st.session_state.voice_choice = VN_VOICE_KEYS[0]


# =====================================================================================
# 6. GIAO DIỆN CHÍNH (UI LAYOUT)
# =====================================================================================
st.title("🎙️ Trình Tạo Giọng Đọc AI Đa Chủ Đề")
st.caption(
    "Chuyển văn bản thành giọng nói tự nhiên bằng công nghệ Edge-TTS của Microsoft - "
    "Miễn phí 100%, không giới hạn, không cần API key. Hoặc dùng thêm ElevenLabs để có "
    "cảm xúc thật, tiếng cười tự nhiên và giọng Adam đang hot trend."
)

engine_choice = st.radio(
    "🔊 Công cụ tạo giọng",
    options=["🆓 Edge-TTS (miễn phí, mô phỏng cảm xúc)", "✨ ElevenLabs (có phí, cảm xúc thật/giọng Adam)"],
    horizontal=True,
    key="tts_engine",
)
use_elevenlabs = engine_choice.startswith("✨")

eleven_api_key = ""
eleven_voice_map = {}
eleven_model = "eleven_v3"
if use_elevenlabs:
    col_key, col_model = st.columns([2, 1])
    with col_key:
        eleven_api_key = st.text_input(
            "ElevenLabs API Key",
            type="password",
            help="Lấy tại elevenlabs.io -> Profile -> API Keys. Key chỉ dùng trong phiên "
                 "làm việc này, không được lưu lại.",
        )
    with col_model:
        eleven_model = st.selectbox(
            "Model", ["eleven_v3", "eleven_multilingual_v2", "eleven_turbo_v2_5"],
            help="eleven_v3: đọc được tag cảm xúc [cười], [thì thầm]... trực tiếp trong câu.",
        )
    if eleven_api_key:
        try:
            voice_list = eleven_list_voices(eleven_api_key)
            eleven_voice_map = {name: vid for name, vid in voice_list}
        except Exception as e:
            st.error(f"Không lấy được danh sách giọng ElevenLabs: {e}")
    else:
        st.info("Nhập API key ở trên để tải danh sách giọng thật (gồm cả giọng Adam).")
    if eleven_api_key and not eleven_voice_map:
        st.warning("Chưa tải được giọng nào — kiểm tra lại API key.")
    elif eleven_api_key:
        st.caption(f"Đã tải {len(eleven_voice_map)} giọng từ workspace ElevenLabs của bạn.")

app_mode = st.radio(
    "🎬 Chế độ tạo giọng đọc",
    options=["🗣️ Một giọng (Đơn)", "👥 Hội thoại nhiều giọng (2-3 người)"],
    horizontal=True,
    key="app_mode",
)
st.divider()

# =====================================================================================
# CHẾ ĐỘ 1: MỘT GIỌNG (ĐƠN)
# =====================================================================================
if app_mode == "🗣️ Một giọng (Đơn)":
    col_settings, col_content = st.columns([1, 2], gap="large")

    with col_settings:
        st.subheader("⚙️ Cấu Hình Giọng Đọc")

        show_foreign = st.checkbox(
            "🌐 Hiện thêm giọng tiếng Anh / Anh-Anh (tuỳ chọn)",
            value=False,
            key="show_foreign_voices",
            on_change=_on_toggle_foreign_voices,
        )
        voice_options = list(VOICES.keys()) if show_foreign else VN_VOICE_KEYS

        voice_label = st.selectbox(
            "🎤 Chọn giọng đọc",
            options=voice_options,
            key="voice_choice",
            help="Chọn giọng đọc phù hợp với chủ đề nội dung của bạn.",
        )
        voice_info = VOICES[voice_label]
        st.info(voice_info["desc"], icon="🗣️")
        if not show_foreign:
            st.caption(
                "💡 Edge-TTS (Microsoft) hiện chỉ phát hành chính thức **2 giọng tiếng Việt** - "
                "Nam Minh (nam) và Hoài My (nữ). Đây là giới hạn từ phía Microsoft, không phải "
                "giới hạn của ứng dụng. Tick ô trên nếu cần thêm giọng tiếng Anh / Anh-Anh."
            )

        eleven_voice_id_single = ""
        if use_elevenlabs:
            if eleven_voice_map:
                names_e = list(eleven_voice_map.keys())
                default_idx_e = 0
                for idx_e, nm in enumerate(names_e):
                    if "adam" in nm.lower():
                        default_idx_e = idx_e
                        break
                eleven_label_single = st.selectbox(
                    "✨ Chọn giọng ElevenLabs", names_e, index=default_idx_e, key="eleven_voice_single"
                )
                eleven_voice_id_single = eleven_voice_map[eleven_label_single]
            else:
                st.warning("Nhập API key ElevenLabs ở trên để chọn giọng.")

        st.markdown("##### 📋 Kịch Bản Mẫu Theo Chủ Đề")
        topic_choice = st.selectbox(
            "Chọn nhanh một kịch bản mẫu (hoặc tự nhập văn bản)",
            options=TOPIC_OPTIONS,
            key="template_choice",
            on_change=_apply_template,
            index=0,
        )

        if topic_choice != "✍️ Tự nhập văn bản tự do":
            st.selectbox(
                "🗺️ Chọn vùng miền cho kịch bản",
                options=list(REGIONS.keys()),
                key="region_choice",
                on_change=_apply_template,
                index=0,
                help=(
                    "Nội dung kịch bản (địa danh, dòng sông, thành phố...) sẽ được tùy biến theo "
                    "vùng miền bạn chọn."
                ),
            )

        st.markdown("---")
        st.markdown("##### 🎛️ Tùy Chỉnh Âm Thanh")

        rate_value = st.slider("⚡ Tốc độ đọc (Rate)", min_value=-50, max_value=50, value=0, step=1, format="%d%%")
        pitch_value = st.slider("🎵 Cao độ / Độ trầm (Pitch)", min_value=-20, max_value=20, value=0, step=1, format="%d Hz")
        st.caption(f"Thông số hiện tại: Rate = **{rate_value:+d}%** | Pitch = **{pitch_value:+d}Hz**")

    with col_content:
        st.subheader("📝 Nội Dung Kịch Bản")

        text_input = st.text_area(
            label="Văn bản cần chuyển thành giọng nói",
            key="script_text",
            height=320,
            placeholder="Nhập hoặc dán văn bản của bạn vào đây, hoặc chọn một kịch bản mẫu ở cột bên trái...",
        )

        char_count = len(text_input.strip())
        st.caption(f"Số ký tự: {char_count}")

        generate_clicked = st.button(
            "🚀 Tạo Giọng Đọc Ngay", type="primary", use_container_width=True, disabled=(char_count == 0),
        )

        if generate_clicked:
            if char_count == 0:
                st.warning("⚠️ Vui lòng nhập văn bản trước khi tạo giọng đọc.")
            elif use_elevenlabs and (not eleven_api_key or not eleven_voice_id_single):
                st.error("❌ Thiếu API key hoặc chưa chọn giọng ElevenLabs.")
            else:
                try:
                    with st.spinner("🎧 Đang xử lý và tạo giọng đọc, vui lòng chờ trong giây lát..."):
                        if use_elevenlabs:
                            audio_result = eleven_tts_speak(
                                text_input, eleven_voice_id_single, eleven_api_key, eleven_model
                            )
                        else:
                            audio_result = generate_voice(
                                text=text_input, voice_id=voice_info["id"],
                                rate_value=rate_value, pitch_value=pitch_value,
                            )

                    if audio_result:
                        st.session_state.audio_bytes = audio_result
                        st.session_state.last_voice_label = voice_label
                        st.success("✅ Tạo giọng đọc thành công!")
                    else:
                        st.error("❌ Không nhận được dữ liệu âm thanh. Vui lòng thử lại.")
                except Exception as e:
                    st.error(f"❌ Đã xảy ra lỗi trong quá trình tạo giọng đọc: {e}")

# =====================================================================================
# CHẾ ĐỘ 2: HỘI THOẠI NHIỀU GIỌNG (2-3 NGƯỜI NÓI CHUYỆN)
# =====================================================================================
else:
    st.subheader("👥 Tạo Hội Thoại Nhiều Giọng")
    st.caption(
        "Tạo một đoạn audio có 2-3 người nói chuyện với nhau, mỗi người một giọng riêng, tự "
        "động ghép nối liền mạch thành một file MP3 duy nhất."
    )

    num_speakers = st.radio("Số người trong hội thoại", options=[2, 3], horizontal=True, key="num_speakers")

    default_names = ["Người 1", "Người 2", "Người 3"]
    default_voice_keys = [VN_VOICE_KEYS[0], VN_VOICE_KEYS[1], VN_VOICE_KEYS[0]]
    default_pitch_offsets = [0, 0, 8]

    speaker_configs = []
    speaker_cols = st.columns(num_speakers)
    for i in range(num_speakers):
        with speaker_cols[i]:
            st.markdown(f"**Người nói #{i + 1}**")
            name = st.text_input("Tên", value=default_names[i], key=f"speaker_name_{i}")
            voice_sel = st.selectbox(
                "Giọng đọc", options=list(VOICES.keys()),
                index=list(VOICES.keys()).index(default_voice_keys[i]), key=f"speaker_voice_{i}",
            )
            pitch_offset = st.slider(
                "Cao độ riêng (Hz)", -20, 20, default_pitch_offsets[i], key=f"speaker_pitch_{i}",
                help="Chỉnh lệch cao độ để phân biệt 2 người nói dùng chung 1 giọng gốc.",
            )
            eleven_voice_id_i = ""
            if use_elevenlabs:
                if eleven_voice_map:
                    names_e = list(eleven_voice_map.keys())
                    idx_e = min(i, len(names_e) - 1)
                    eleven_label_i = st.selectbox(
                        "✨ Giọng ElevenLabs", names_e, index=idx_e, key=f"eleven_speaker_voice_{i}"
                    )
                    eleven_voice_id_i = eleven_voice_map[eleven_label_i]
                else:
                    st.caption("Nhập API key ElevenLabs ở trên trước")
            speaker_configs.append({
                "name": name.strip() or default_names[i],
                "voice_id": VOICES[voice_sel]["id"],
                "pitch_offset": pitch_offset,
                "eleven_voice_id": eleven_voice_id_i,
            })

    if num_speakers == 3:
        st.caption(
            "💡 Vì Edge-TTS chỉ có 2 giọng tiếng Việt, người thứ 3 mặc định dùng lại giọng Nam "
            "Minh với cao độ lệch để nghe khác biệt hơn."
        )

    st.markdown("##### 📋 Kịch Bản Mẫu Hội Thoại Theo Chủ Đề")

    def _apply_dialogue_template():
        topic = st.session_state.get("dialogue_topic_choice", DIALOGUE_TOPIC_OPTIONS[0])
        n = st.session_state.get("num_speakers", 2)
        names = [
            (st.session_state.get(f"speaker_name_{i}", "") or default_names[i]).strip() or default_names[i]
            for i in range(n)
        ]
        st.session_state.dialogue_script = build_dialogue_template(topic, names)
        st.session_state.audio_bytes = None

    st.selectbox(
        "Chọn nhanh một kịch bản hội thoại mẫu (hoặc tự soạn)",
        options=DIALOGUE_TOPIC_OPTIONS, key="dialogue_topic_choice", on_change=_apply_dialogue_template, index=0,
    )
    st.button(
        "🔄 Tải lại kịch bản mẫu (theo chủ đề & tên/số người hiện tại)",
        on_click=_apply_dialogue_template,
    )

    if "dialogue_script" not in st.session_state:
        _apply_dialogue_template()

    st.markdown("##### 📝 Kịch Bản Hội Thoại")
    st.caption(
        "Mỗi dòng bắt đầu bằng **đúng tên người nói** + dấu hai chấm. Chèn thẻ như `[vui]`, "
        "`[buồn]`, `[cười]`... ngay trong câu để đổi cảm xúc giọng đọc."
    )

    with st.expander("📌 Hướng dẫn: chèn cảm xúc vào lời thoại"):
        st.markdown(
            "Chèn thẻ dạng `[tên_cảm_xúc]` vào giữa câu thoại. Ví dụ:\n\n"
            "`Lan: [buồn] Hôm nay tớ chẳng vui chút nào... [vui] nhưng gặp cậu tớ thấy khá hơn rồi!`"
        )
        for key, cfg in EMOTION_TAGS.items():
            st.caption(f"`[{key}]` — {cfg['label']}")

    dialogue_script = st.text_area(
        "Nội dung hội thoại", key="dialogue_script", height=280, placeholder="Người 1: ...\nNgười 2: ...",
    )

    col_rate, col_pitch = st.columns(2)
    with col_rate:
        dialogue_rate = st.slider("⚡ Tốc độ đọc chung (Rate)", -50, 50, 0, step=1, format="%d%%", key="dialogue_rate")
    with col_pitch:
        dialogue_pitch = st.slider("🎵 Cao độ nền chung (Pitch)", -20, 20, 0, step=1, format="%d Hz", key="dialogue_pitch")

    dialogue_char_count = len(dialogue_script.strip())
    generate_dialogue_clicked = st.button(
        "🚀 Tạo Hội Thoại Ngay", type="primary", use_container_width=True, disabled=(dialogue_char_count == 0),
    )

    if generate_dialogue_clicked:
        speaker_names = [s["name"] for s in speaker_configs]

        if use_elevenlabs:
            if not eleven_api_key:
                st.error("❌ Thiếu API key ElevenLabs.")
            else:
                turns_raw = parse_dialogue_script_raw(dialogue_script, speaker_names)
                if not turns_raw:
                    st.warning("⚠️ Không nhận diện được lượt thoại nào. Kiểm tra tên người nói + dấu hai chấm.")
                else:
                    try:
                        with st.spinner(f"🎧 Đang tạo {len(turns_raw)} lượt thoại (ElevenLabs)..."):
                            eleven_speaker_voice_map = {s["name"]: s["eleven_voice_id"] for s in speaker_configs}
                            audio_result = eleven_generate_dialogue_audio(
                                turns_raw, eleven_speaker_voice_map, eleven_api_key, eleven_model
                            )
                        if audio_result:
                            st.session_state.audio_bytes = audio_result
                            st.session_state.last_voice_label = f"HoiThoai_{num_speakers}Nguoi_Eleven"
                            st.success(f"✅ Đã tạo xong hội thoại gồm {len(turns_raw)} lượt nói!")
                        else:
                            st.error("❌ Không nhận được dữ liệu âm thanh. Vui lòng thử lại.")
                    except Exception as e:
                        st.error(f"❌ Đã xảy ra lỗi khi tạo hội thoại: {e}")
        else:
            turns = parse_dialogue_script(dialogue_script, speaker_names)
            if not turns:
                st.warning("⚠️ Không nhận diện được lượt thoại nào. Kiểm tra tên người nói + dấu hai chấm.")
            else:
                used_speakers = {spk for spk, _ in turns}
                missing_speakers = [name for name in speaker_names if name not in used_speakers]
                if missing_speakers:
                    st.warning(
                        "⚠️ (Những) người nói sau không xuất hiện trong kịch bản: "
                        f"{', '.join(missing_speakers)}."
                    )
                try:
                    with st.spinner(f"🎧 Đang tạo {len(turns)} lượt thoại và ghép thành 1 file..."):
                        speaker_voice_map = {s["name"]: s["voice_id"] for s in speaker_configs}
                        speaker_pitch_map = {s["name"]: s["pitch_offset"] for s in speaker_configs}
                        audio_result = generate_dialogue_audio(
                            turns, speaker_voice_map, speaker_pitch_map, dialogue_rate, dialogue_pitch,
                        )
                    if audio_result:
                        st.session_state.audio_bytes = audio_result
                        st.session_state.last_voice_label = f"HoiThoai_{num_speakers}Nguoi"
                        st.success(f"✅ Đã tạo xong hội thoại gồm {len(turns)} lượt nói!")
                    else:
                        st.error("❌ Không nhận được dữ liệu âm thanh. Vui lòng thử lại.")
                except Exception as e:
                    st.error(f"❌ Đã xảy ra lỗi khi tạo hội thoại: {e}")

# =====================================================================================
# KHU VỰC PHÁT & TẢI FILE (DÙNG CHUNG CHO CẢ 2 CHẾ ĐỘ)
# =====================================================================================
if st.session_state.audio_bytes:
    st.divider()
    st.subheader("🔊 Nghe Thử & Tải Xuống")
    st.audio(st.session_state.audio_bytes, format="audio/mp3")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_voice_name = (
        (st.session_state.last_voice_label or "GiongDoc")
        .split(" - ")[0].replace("🇻🇳", "").replace("🇺🇸", "").replace("🇬🇧", "").strip().replace(" ", "_")
    )
    file_name = f"GiongDoc_{safe_voice_name}_{timestamp}.mp3"

    st.download_button(
        label="⬇️ Tải File MP3 Về Máy", data=st.session_state.audio_bytes,
        file_name=file_name, mime="audio/mpeg", use_container_width=True,
    )

# =====================================================================================
# 7. FOOTER
# =====================================================================================
st.divider()
st.caption(
    "🎙️ Trình Tạo Giọng Đọc AI Đa Chủ Đề — Xây dựng bằng Streamlit, edge-tts (Microsoft) "
    "và ElevenLabs. Xưởng Giọng Đọc — Thắng Võ | Solar 3T · Chợ App 3T."
)
