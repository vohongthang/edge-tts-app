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
from datetime import datetime

import edge_tts
import streamlit as st

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
# 2. DANH MỤC GIỌNG ĐỌC (VOICE DICT)
# =====================================================================================
# Key: Tên hiển thị trên giao diện | Value: (voice_id, mô tả ngắn)
VOICES = {
    "🇻🇳 Nam Minh - Nam (Miền Bắc)": {
        "id": "vi-VN-NamMinhNeural",
        "desc": "Giọng nam miền Bắc, trầm ấm, chuẩn mực. Phù hợp: Bản tin, Bất động sản, Doanh nghiệp.",
    },
    "🇻🇳 Hoài My - Nữ (Miền Bắc)": {
        "id": "vi-VN-HoaiMyNeural",
        "desc": "Giọng nữ miền Bắc, truyền cảm, nhẹ nhàng. Phù hợp: Phóng sự, Review, Storytelling.",
    },
    "🇺🇸 Jenny - Female (US English)": {
        "id": "en-US-JennyNeural",
        "desc": "Giọng nữ tiếng Anh Mỹ chuẩn, tự nhiên. Phù hợp: Nội dung tiếng Anh, E-learning.",
    },
    "🇺🇸 Guy - Male (US English)": {
        "id": "en-US-GuyNeural",
        "desc": "Giọng nam tiếng Anh Mỹ, rõ ràng, chuyên nghiệp. Phù hợp: Thuyết trình, Quảng cáo tiếng Anh.",
    },
}

# =====================================================================================
# 3. KHO KỊCH BẢN MẪU THEO CHỦ ĐỀ x VÙNG MIỀN (TEMPLATES SELECTOR)
# =====================================================================================
# Lưu ý: Edge-TTS chỉ cung cấp 2 giọng tiếng Việt (Nam Minh, Hoài My - đều là giọng
# chuẩn miền Bắc), Microsoft chưa có giọng đọc riêng theo phương ngữ từng vùng miền.
# Vì vậy phần "vùng miền" dưới đây tùy biến NỘI DUNG kịch bản (địa danh, sông, thành
# phố...) theo từng địa phương, còn giọng đọc vẫn chọn ở mục Cấu Hình Giọng Đọc.

TOPIC_OPTIONS = [
    "🏢 Bất Động Sản (Sang trọng / Thôi thúc)",
    "📰 Tin Tức / Phóng Sự",
    "📖 Review / Kể Chuyện",
    "✍️ Tự nhập văn bản tự do",
]

# Thông tin đặc trưng của từng vùng miền, dùng để dựng kịch bản
REGIONS = {
    "Nghệ An (TP Vinh)": {"noun_phrase": "thành phố Vinh, xứ Nghệ", "landmark": "sông Lam"},
    "Huế (Cố đô)": {"noun_phrase": "cố đô Huế nghìn năm văn hiến", "landmark": "sông Hương"},
    "Đà Nẵng": {"noun_phrase": "thành phố đáng sống Đà Nẵng", "landmark": "sông Hàn"},
    "Hà Nội": {"noun_phrase": "thủ đô Hà Nội ngàn năm văn hiến", "landmark": "sông Hồng"},
    "TP. Hồ Chí Minh": {"noun_phrase": "thành phố Hồ Chí Minh năng động", "landmark": "sông Sài Gòn"},
}

# Kịch bản biên soạn riêng, chi tiết cho 2 vùng miền trọng tâm: Nghệ An & Huế
CURATED_SCRIPTS = {
    ("🏢 Bất Động Sản (Sang trọng / Thôi thúc)", "Nghệ An (TP Vinh)"): (
        "Tọa lạc tại vị trí đắc địa bậc nhất thành phố Vinh, dự án khu đô thị mới "
        "do Sun Group phát triển tự hào mang đến một chuẩn sống thượng lưu chưa từng có "
        "tại xứ Nghệ.\n\n"
        "Không chỉ là nơi an cư, đây còn là biểu tượng phồn vinh mới - nơi hội tụ trọn vẹn "
        "hệ sinh thái tiện ích đẳng cấp quốc tế: quảng trường ánh sáng, phố đi bộ thương mại, "
        "công viên trung tâm, trường học liên cấp và bệnh viện quốc tế, tất cả trong tầm tay "
        "cư dân.\n\n"
        "Với thiết kế kiến trúc tân cổ điển sang trọng, cùng chính sách bán hàng ưu đãi vượt trội "
        "dành riêng cho một trăm khách hàng đầu tiên, đây chính là cơ hội đầu tư vàng không thể "
        "bỏ lỡ trong năm nay.\n\n"
        "Cơ hội sở hữu bất động sản triệu đô đang đến rất gần. Quý khách hàng vui lòng liên hệ "
        "ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn "
        "và giữ chỗ thiện đầu tiên. Số không chín bảy bảy chấm sáu tám bảy chấm hai hai bảy - "
        "cơ hội chỉ dành cho những khách hàng nhanh tay nhất."
    ),
    ("🏢 Bất Động Sản (Sang trọng / Thôi thúc)", "Huế (Cố đô)"): (
        "Tọa lạc bên dòng sông Hương thơ mộng, ngay giữa lòng cố đô Huế nghìn năm văn hiến, "
        "dự án khu đô thị ven sông tự hào kiến tạo một chuẩn sống an nhiên, sang trọng bậc nhất "
        "miền Trung.\n\n"
        "Không chỉ là chốn an cư, đây còn là không gian sống di sản đương đại - nơi hội tụ công "
        "viên cảnh quan ven sông, phố đi bộ ẩm thực cung đình, quảng trường văn hóa và hệ thống "
        "tiện ích nghỉ dưỡng chuẩn năm sao, tất cả trong tầm tay cư dân.\n\n"
        "Với thiết kế kiến trúc pha trộn tinh hoa cung đình Huế và phong cách hiện đại, cùng chính "
        "sách ưu đãi đặc biệt dành riêng cho những khách hàng đặt chỗ sớm nhất, đây chính là cơ hội "
        "đầu tư hiếm có giữa lòng cố đô.\n\n"
        "Cơ hội sở hữu bất động sản ven sông Hương đang đến rất gần. Quý khách hàng vui lòng liên hệ "
        "ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư vấn "
        "và giữ chỗ sớm nhất. Số không chín bảy bảy chấm sáu tám bảy chấm hai hai bảy - cơ hội chỉ "
        "dành cho những khách hàng nhanh tay nhất."
    ),
    ("📰 Tin Tức / Phóng Sự", "Nghệ An (TP Vinh)"): (
        "Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi bật "
        "về tốc độ phát triển hạ tầng tại tỉnh Nghệ An.\n\n"
        "Trong những năm gần đây, thành phố Vinh đang chuyển mình mạnh mẽ để trở thành trung tâm "
        "kinh tế, văn hóa của khu vực Bắc Trung Bộ. Hàng loạt tuyến đường huyết mạch được mở rộng, "
        "nhiều khu đô thị mới quy mô lớn lần lượt được khởi công, kéo theo làn sóng dịch chuyển dân cư "
        "và dòng vốn đầu tư đổ về ngày càng mạnh mẽ.\n\n"
        "Theo đánh giá của giới chuyên gia, quy hoạch mở rộng địa giới hành chính cùng với sự xuất hiện "
        "của các nhà đầu tư chiến lược đã và đang tạo ra một diện mạo hoàn toàn mới cho đô thị Vinh, "
        "hứa hẹn đưa thành phố trở thành điểm sáng đáng sống bậc nhất miền Trung trong thập kỷ tới.\n\n"
        "Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý vị "
        "trong những bản tin tiếp theo."
    ),
    ("📰 Tin Tức / Phóng Sự", "Huế (Cố đô)"): (
        "Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi bật "
        "về tốc độ phát triển hạ tầng tại thành phố Huế.\n\n"
        "Trong những năm gần đây, cố đô Huế đang chuyển mình mạnh mẽ để trở thành đô thị di sản, "
        "văn hóa và du lịch đặc trưng của cả nước. Hàng loạt tuyến đường ven sông Hương được chỉnh "
        "trang, nhiều khu đô thị mới quy mô lớn lần lượt được khởi công, kéo theo làn sóng dịch chuyển "
        "dân cư và dòng vốn đầu tư đổ về ngày càng mạnh mẽ.\n\n"
        "Theo đánh giá của giới chuyên gia, việc Huế trở thành thành phố trực thuộc Trung ương cùng "
        "với chiến lược bảo tồn gắn liền với phát triển đã và đang tạo ra một diện mạo hoàn toàn mới "
        "cho đô thị cố đô, hứa hẹn đưa Huế trở thành điểm sáng đáng sống bậc nhất miền Trung trong "
        "thập kỷ tới.\n\n"
        "Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý vị "
        "trong những bản tin tiếp theo."
    ),
    ("📖 Review / Kể Chuyện", "Nghệ An (TP Vinh)"): (
        "Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven sông Lam, và cảm giác đầu tiên khi "
        "bước chân xuống xe là một sự bình yên đến lạ.\n\n"
        "Gió từ sông thổi vào mát rượi, xa xa là hàng cây xanh rợp bóng chạy dọc theo bờ kè, tiếng "
        "trẻ con nô đùa trong công viên nội khu hòa cùng tiếng chim hót khiến tôi bất giác mỉm cười. "
        "Không gian sống nơi đây thực sự khác biệt so với sự ồn ào, ngột ngạt của phố thị mà tôi vẫn "
        "quen thuộc mỗi ngày.\n\n"
        "Ngồi nhâm nhi ly cà phê tại quán ven sông, ngắm hoàng hôn buông xuống mặt nước lấp lánh, tôi "
        "chợt nhận ra đây chính xác là hình ảnh chốn an cư mà bao người vẫn hằng mơ ước - nơi con người "
        "được sống chậm lại, gần gũi với thiên nhiên nhưng vẫn không xa rời tiện nghi hiện đại.\n\n"
        "Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị ven "
        "sông Lam này rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
    ),
    ("📖 Review / Kể Chuyện", "Huế (Cố đô)"): (
        "Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven sông Hương, và cảm giác đầu tiên khi "
        "bước chân xuống xe là một sự tĩnh tại đến lạ.\n\n"
        "Gió từ sông thổi vào mát rượi, xa xa là những nhịp cầu bắc qua dòng Hương giang, tiếng "
        "chuông chùa vọng lại từ xa hòa cùng tiếng đò dọc sông khiến tôi bất giác chậm lại. Không "
        "gian sống nơi đây mang một vẻ đẹp trầm mặc, sâu lắng rất riêng của xứ Huế mộng mơ.\n\n"
        "Ngồi nhâm nhi ly trà sen bên hiên nhà ven sông, ngắm hoàng hôn buông xuống mặt nước lấp "
        "lánh, tôi chợt nhận ra đây chính xác là hình ảnh chốn an cư mà bao người vẫn hằng mơ ước - "
        "nơi con người được sống chậm lại, gần gũi với văn hóa cố đô nhưng vẫn không xa rời tiện "
        "nghi hiện đại.\n\n"
        "Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị ven "
        "sông Hương này rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
    ),
}


def _build_generic_script(topic_label: str, region_label: str) -> str:
    """Dựng kịch bản theo mẫu chung cho các vùng miền chưa có bản biên soạn riêng
    (Đà Nẵng, Hà Nội, TP. Hồ Chí Minh...), dựa trên tên thành phố / dòng sông đặc trưng."""
    info = REGIONS[region_label]
    city = info["noun_phrase"]
    river = info["landmark"]

    if topic_label.startswith("🏢"):
        return (
            f"Tọa lạc bên dòng {river} thơ mộng, ngay giữa lòng {city}, dự án khu đô thị mới "
            f"tự hào mang đến một chuẩn sống thượng lưu chưa từng có tại khu vực.\n\n"
            f"Không chỉ là nơi an cư, đây còn là biểu tượng phồn vinh mới - nơi hội tụ trọn vẹn hệ "
            f"sinh thái tiện ích đẳng cấp quốc tế: quảng trường ánh sáng, phố đi bộ thương mại, công "
            f"viên trung tâm, trường học liên cấp và bệnh viện quốc tế, tất cả trong tầm tay cư dân.\n\n"
            f"Với thiết kế kiến trúc sang trọng cùng chính sách bán hàng ưu đãi vượt trội dành riêng "
            f"cho một trăm khách hàng đầu tiên, đây chính là cơ hội đầu tư vàng không thể bỏ lỡ trong "
            f"năm nay.\n\n"
            f"Cơ hội sở hữu bất động sản ven {river} đang đến rất gần. Quý khách hàng vui lòng liên hệ "
            f"ngay hotline, hoặc Zalo không không chín bảy bảy, sáu tám bảy, hai hai bảy để được tư "
            f"vấn và giữ chỗ sớm nhất. Số không chín bảy bảy chấm sáu tám bảy chấm hai hai bảy."
        )
    if topic_label.startswith("📰"):
        return (
            f"Bản tin chuyển động đô thị hôm nay xin gửi tới quý vị và các bạn những thông tin nổi "
            f"bật về tốc độ phát triển hạ tầng tại {city}.\n\n"
            f"Trong những năm gần đây, khu vực này đang chuyển mình mạnh mẽ để trở thành một trong "
            f"những trung tâm kinh tế, văn hóa quan trọng của cả nước. Hàng loạt tuyến đường huyết "
            f"mạch được mở rộng, nhiều khu đô thị mới quy mô lớn lần lượt được khởi công, kéo theo "
            f"làn sóng dịch chuyển dân cư và dòng vốn đầu tư đổ về ngày càng mạnh mẽ.\n\n"
            f"Theo đánh giá của giới chuyên gia, quy hoạch mở rộng cùng với sự xuất hiện của các nhà "
            f"đầu tư chiến lược đã và đang tạo ra một diện mạo hoàn toàn mới cho khu vực, hứa hẹn trở "
            f"thành điểm sáng đáng sống trong thập kỷ tới.\n\n"
            f"Chương trình chuyển động đô thị đến đây xin tạm dừng. Xin kính chào và hẹn gặp lại quý "
            f"vị trong những bản tin tiếp theo."
        )
    # Review / Kể chuyện
    return (
        f"Có một buổi chiều, tôi tình cờ ghé qua khu dân cư ven {river}, và cảm giác đầu tiên khi "
        f"bước chân xuống xe là một sự bình yên đến lạ.\n\n"
        f"Gió từ sông thổi vào mát rượi, xa xa là hàng cây xanh rợp bóng chạy dọc theo bờ kè, tiếng "
        f"trẻ con nô đùa trong công viên nội khu khiến tôi bất giác mỉm cười. Không gian sống nơi "
        f"đây thực sự khác biệt so với sự ồn ào, ngột ngạt của phố thị mà tôi vẫn quen thuộc mỗi "
        f"ngày.\n\n"
        f"Ngồi nhâm nhi ly cà phê ven sông, ngắm hoàng hôn buông xuống mặt nước lấp lánh, tôi chợt "
        f"nhận ra đây chính xác là hình ảnh chốn an cư mà bao người vẫn hằng mơ ước.\n\n"
        f"Nếu bạn cũng đang tìm kiếm một nơi để trở về sau ngày dài mệt mỏi, tôi nghĩ khu đô thị "
        f"ven {river} này tại {city} rất xứng đáng để bạn dành thời gian ghé thăm và trải nghiệm."
    )


def get_script_text(topic_label: str, region_label: str) -> str:
    """Trả về nội dung kịch bản tương ứng với chủ đề + vùng miền đã chọn."""
    if topic_label == "✍️ Tự nhập văn bản tự do":
        return ""
    key = (topic_label, region_label)
    if key in CURATED_SCRIPTS:
        return CURATED_SCRIPTS[key]
    return _build_generic_script(topic_label, region_label)

# =====================================================================================
# 4. XỬ LÝ BẤT ĐỒNG BỘ - GỌI EDGE-TTS
# =====================================================================================
async def _synthesize_speech(text: str, voice_id: str, rate: str, pitch: str) -> bytes:
    """
    Kết nối tới edge-tts.Communicate và stream dữ liệu âm thanh dạng bytes.
    Trả về toàn bộ nội dung audio (định dạng MP3) dưới dạng bytes.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate, pitch=pitch)
    audio_buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
        # chunk["type"] == "WordBoundary" -> bỏ qua, không cần cho việc xuất file audio

    return audio_buffer.getvalue()


def run_async_task(coro):
    """
    Wrapper an toàn để chạy một coroutine bất đồng bộ (asyncio) bên trong
    môi trường đồng bộ của Streamlit, tránh lỗi "no current event loop"
    có thể xảy ra tùy theo phiên bản Python / hệ điều hành.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def generate_voice(text: str, voice_id: str, rate_value: int, pitch_value: int) -> bytes:
    """Chuẩn hóa tham số rate/pitch theo định dạng edge-tts yêu cầu rồi gọi TTS."""
    rate_str = f"{rate_value:+d}%"
    pitch_str = f"{pitch_value:+d}Hz"
    return run_async_task(_synthesize_speech(text, voice_id, rate_str, pitch_str))


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
    """Callback: khi người dùng đổi chủ đề hoặc vùng miền, nạp lại nội dung mẫu tương ứng."""
    topic_choice = st.session_state.template_choice
    region_choice = st.session_state.get("region_choice", DEFAULT_REGION_KEY)
    st.session_state.script_text = get_script_text(topic_choice, region_choice)
    # Xóa audio cũ vì nội dung kịch bản đã thay đổi
    st.session_state.audio_bytes = None


# =====================================================================================
# 6. GIAO DIỆN CHÍNH (UI LAYOUT)
# =====================================================================================
st.title("🎙️ Trình Tạo Giọng Đọc AI Đa Chủ Đề")
st.caption(
    "Chuyển văn bản thành giọng nói tự nhiên bằng công nghệ Edge-TTS của Microsoft - "
    "Miễn phí 100%, không giới hạn, không cần API key."
)
st.divider()

col_settings, col_content = st.columns([1, 2], gap="large")

# ---------------------------- CỘT TRÁI: CẤU HÌNH ----------------------------
with col_settings:
    st.subheader("⚙️ Cấu Hình Giọng Đọc")

    voice_label = st.selectbox(
        "🎤 Chọn giọng đọc",
        options=list(VOICES.keys()),
        key="voice_choice",
        help="Chọn giọng đọc phù hợp với chủ đề nội dung của bạn.",
    )
    voice_info = VOICES[voice_label]
    st.info(voice_info["desc"], icon="🗣️")

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
                "vùng miền bạn chọn. Nghệ An và Huế có kịch bản biên soạn riêng chi tiết; các "
                "vùng miền khác dùng mẫu chung có thể chỉnh sửa lại."
            ),
        )
        st.caption(
            "🎙️ Lưu ý: Edge-TTS hiện chỉ có 2 giọng tiếng Việt (Nam Minh, Hoài My) theo chuẩn "
            "phát âm miền Bắc - chưa có giọng đọc riêng theo phương ngữ từng vùng."
        )

    st.markdown("---")
    st.markdown("##### 🎛️ Tùy Chỉnh Âm Thanh")

    rate_value = st.slider(
        "⚡ Tốc độ đọc (Rate)",
        min_value=-50,
        max_value=50,
        value=0,
        step=1,
        format="%d%%",
        help="Điều chỉnh tốc độ đọc nhanh hoặc chậm hơn so với mặc định.",
    )

    pitch_value = st.slider(
        "🎵 Cao độ / Độ trầm (Pitch)",
        min_value=-20,
        max_value=20,
        value=0,
        step=1,
        format="%d Hz",
        help="Điều chỉnh giọng đọc cao hoặc trầm hơn so với mặc định.",
    )

    st.caption(f"Thông số hiện tại: Rate = **{rate_value:+d}%** | Pitch = **{pitch_value:+d}Hz**")

# ---------------------------- CỘT PHẢI: NỘI DUNG & KẾT QUẢ ----------------------------
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
        "🚀 Tạo Giọng Đọc Ngay",
        type="primary",
        use_container_width=True,
        disabled=(char_count == 0),
    )

    if generate_clicked:
        if char_count == 0:
            st.warning("⚠️ Vui lòng nhập văn bản trước khi tạo giọng đọc.")
        else:
            try:
                with st.spinner("🎧 Đang xử lý và tạo giọng đọc, vui lòng chờ trong giây lát..."):
                    audio_result = generate_voice(
                        text=text_input,
                        voice_id=voice_info["id"],
                        rate_value=rate_value,
                        pitch_value=pitch_value,
                    )

                if audio_result:
                    st.session_state.audio_bytes = audio_result
                    st.session_state.last_voice_label = voice_label
                    st.success("✅ Tạo giọng đọc thành công!")
                else:
                    st.error("❌ Không nhận được dữ liệu âm thanh. Vui lòng thử lại.")
            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi trong quá trình tạo giọng đọc: {e}")

    # ---------------------------- KHU VỰC PHÁT & TẢI FILE ----------------------------
    if st.session_state.audio_bytes:
        st.markdown("---")
        st.subheader("🔊 Nghe Thử & Tải Xuống")

        st.audio(st.session_state.audio_bytes, format="audio/mp3")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_voice_name = (
            (st.session_state.last_voice_label or voice_label)
            .split(" - ")[0]
            .replace("🇻🇳", "")
            .replace("🇺🇸", "")
            .strip()
            .replace(" ", "_")
        )
        file_name = f"GiongDoc_{safe_voice_name}_{timestamp}.mp3"

        st.download_button(
            label="⬇️ Tải File MP3 Về Máy",
            data=st.session_state.audio_bytes,
            file_name=file_name,
            mime="audio/mpeg",
            use_container_width=True,
        )

# =====================================================================================
# 7. FOOTER
# =====================================================================================
st.divider()
st.caption(
    "🎙️ Trình Tạo Giọng Đọc AI Đa Chủ Đề — Xây dựng bằng Streamlit & edge-tts (Microsoft). "
    "Công cụ miễn phí, không thu thập dữ liệu, không cần API key."
)
