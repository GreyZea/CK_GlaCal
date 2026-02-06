import streamlit as st
from rectpack import newPacker
import rectpack.packer as packer
import random

# --- 1. ระบบรหัสผ่าน ---
PASSWORD = "CK3006"


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 GlaCal Master (AI Optimization)")
        pwd = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("รหัสผ่านผิด!")
        return False
    return True


# --- 2. ฟังก์ชันจำลองการตัดแบบสถิติ (Simulation Engine) ---
def run_simulation(stocks, pieces, allowance, trials=50):
    best_overall_results = None
    min_total_waste = float('inf')

    # แสดง progress bar เพื่อให้ผู้ใช้รู้ว่ากำลังคำนวณหลายรอบ
    progress_text = "กำลังจำลองรูปแบบการวางที่คุ้มที่สุด..."
    my_bar = st.progress(0, text=progress_text)

    for trial in range(trials):
        # สลับลำดับชิ้นงานเพื่อหาความเป็นไปได้ใหม่ๆ (Statistical Shuffle)
        current_pieces = pieces.copy()
        random.shuffle(current_pieces)

        temp_packer = newPacker(
            mode=packer.PackingMode.Offline,
            bin_algo=packer.PackingBin.Baf,  # Best Area Fit
            pack_algo=packer.MaxRectsBssf,
            rotation=True
        )

        # ใส่แผ่นคลัง (เรียงแผ่นเล็กไปใหญ่เพื่อให้เลือกใช้แผ่นที่ฟิตก่อน)
        sorted_stocks = sorted(stocks, key=lambda x: x['w'] * x['h'])
        for s in sorted_stocks:
            temp_packer.add_bin(s['w'], s['h'], count=float('inf'))

        for p in current_pieces:
            temp_packer.add_rect(p['w'] + allowance, p['h'] + allowance)

        temp_packer.pack()

        # คำนวณหาความคุ้มค่าของรอบนี้
        total_used_area = 0
        total_bin_area = 0
        current_results = []

        for b in temp_packer:
            if len(b) > 0:
                bin_area = b.width * b.height
                used_area_in_bin = sum((r.width - allowance) * (r.height - allowance) for r in b)
                total_used_area += used_area_in_bin
                total_bin_area += bin_area
                current_results.append({
                    'width': b.width,
                    'height': b.height,
                    'used_area': used_area_in_bin,
                    'rects': [{'w': r.width - allowance, 'h': r.height - allowance} for r in b]
                })

        current_waste = total_bin_area - total_used_area

        # เก็บผลลัพธ์ที่ดีที่สุด (เหลือเศษน้อยที่สุด)
        if current_waste < min_total_waste:
            min_total_waste = current_waste
            best_overall_results = current_results

        my_bar.progress((trial + 1) / trials, text=progress_text)

    my_bar.empty()
    return best_overall_results


# --- 3. UI ---
st.set_page_config(page_title="GlaCal AI Optimizer", layout="wide")

if check_password():
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'ชุดงานที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 1}]}]

    with st.sidebar:
        st.title("📦 คลังกระจก")
        allowance = st.number_input("ระยะเผื่อหัก (นิ้ว)", value=0.125, format="%.4f")
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มแผ่นคลัง", on_click=lambda: st.session_state.stocks.append({'w': 36.0, 'h': 72.0}))

    st.title("🖼️ GlaCal: ระบบคำนวณแบบจำลองสถิติ (Best Overall)")
    st.info("💡 ระบบจะจำลองการวาง 50 รูปแบบที่แตกต่างกัน เพื่อหาทางเลือกที่ประหยัดเนื้อกระจกมากที่สุด")

    for p_idx, proj in enumerate(st.session_state.projects):
        with st.container(border=True):
            proj['name'] = st.text_input("ชื่อโปรเจกต์", value=proj['name'], key=f"pname_{p_idx}")

            for i, it in enumerate(proj['items']):
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([0.35, 0.35, 0.2, 0.1])
                    it['w'] = c1.number_input(f"กว้าง", value=float(it['w']), key=f"w_{p_idx}_{i}")
                    it['h'] = c2.number_input(f"สูง", value=float(it['h']), key=f"h_{p_idx}_{i}")
                    it['qty'] = c3.number_input(f"จำนวน", value=int(it['qty']), min_value=1, key=f"q_{p_idx}_{i}")
                    if c4.button("❌", key=f"del_it_{p_idx}_{i}"):
                        proj['items'].pop(i);
                        st.rerun()

            if st.button(f"🚀 คำนวณหาจุดคุ้มค่าที่สุด", key=f"calc_{p_idx}", type="primary"):
                stocks_data = st.session_state.stocks
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]

                # รันการจำลอง 50 รอบเพื่อหาผลลัพธ์ที่ดีที่สุด
                results = run_simulation(stocks_data, pieces_data, allowance, trials=50)

                if results:
                    total_area_all = sum(s['width'] * s['height'] for s in results)
                    total_used_all = sum(s['used_area'] for s in results)
                    overall_efficiency = (total_used_all / total_area_all) * 100

                    st.success(
                        f"📊 ผลการจำลองที่ดีที่สุด: ใช้ {len(results)} แผ่น | ความคุ้มค่ารวม {overall_efficiency:.1f}%")

                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['width']}x{s['height']}", expanded=True):
                                eff = (s['used_area'] / (s['width'] * s['height'])) * 100
                                st.write(f"📊 ประสิทธิภาพแผ่นนี้: **{eff:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(s['width'] * s['height'] - s['used_area']):.2f}** ตร.นิ้ว")
                                st.progress(min(eff / 100, 1.0))
                                for p in s['rects']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
                else:
                    st.error("❌ ไม่สามารถคำนวณได้ โปรดเช็คขนาดชิ้นงาน")
