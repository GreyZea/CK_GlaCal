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
        st.title("🔒 GlaCal Master (Big-Sheet Priority)")
        pwd = st.text_input("รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("รหัสผ่านผิด!")
        return False
    return True


# --- 2. ฟังก์ชันจำลองการตัด (เน้นแผ่นใหญ่เป็นอันดับแรก) ---
def run_simulation_big_first(stocks, pieces, allowance, trials=50):
    best_overall_results = None
    min_total_waste = float('inf')

    progress_text = "กำลังคำนวณ... (บังคับเลือกใช้แผ่นใหญ่ก่อน)"
    my_bar = st.progress(0, text=progress_text)

    # เรียงคลังจาก "ใหญ่สุดไปเล็กสุด" (Strict Priority)
    priority_stocks = sorted(stocks, key=lambda x: x['w'] * x['h'], reverse=True)

    for trial in range(trials):
        current_pieces = pieces.copy()
        random.shuffle(current_pieces)

        # ใช้ PackingBin.Global เพื่อให้ระบบพิจารณา Bin ตามลำดับที่เราใส่เข้าไป (ซึ่งเราเรียงแผ่นใหญ่ไว้ก่อน)
        packer_engine = newPacker(
            mode=packer.PackingMode.Offline,
            bin_algo=packer.PackingBin.Global,
            pack_algo=packer.MaxRectsBssf,
            rotation=True
        )

        # เพิ่มแผ่นใหญ่เข้าสู่ระบบตามลำดับความสำคัญ
        for s in priority_stocks:
            # ใส่จำนวนแผ่นเผื่อไว้เพื่อให้ระบบเลือกใช้ไซส์ใหญ่จนกว่าจะหมด/ใส่ไม่ได้
            packer_engine.add_bin(s['w'], s['h'], count=100)

        for i, p in enumerate(current_pieces):
            packer_engine.add_rect(p['w'] + allowance, p['h'] + allowance, rid=i)

        packer_engine.pack()

        current_results = []
        total_bin_area = 0
        total_used_area = 0

        for b in packer_engine:
            if len(b) > 0:
                bin_area = b.width * b.height
                used_area_in_bin = sum((r.width - allowance) * (r.height - allowance) for r in b)

                total_bin_area += bin_area
                total_used_area += used_area_in_bin

                current_results.append({
                    'width': b.width,
                    'height': b.height,
                    'used_area': used_area_in_bin,
                    'rects': [{'w': r.width - allowance, 'h': r.height - allowance} for r in b]
                })

        if current_results:
            current_waste = total_bin_area - total_used_area
            if current_waste < min_total_waste:
                min_total_waste = current_waste
                best_overall_results = current_results

        my_bar.progress((trial + 1) / trials, text=progress_text)

    my_bar.empty()
    return best_overall_results


# --- 3. UI ---
st.set_page_config(page_title="GlaCal AI Big-Sheet First", layout="wide")

if check_password():
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'งานตัดชุดที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 1}]}]

    with st.sidebar:
        st.title("⚙️ คลังกระจก")
        allowance = st.number_input("ระยะเผื่อหัก (นิ้ว)", value=0.125, format="%.4f")
        st.divider()
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มขนาดคลัง", on_click=lambda: st.session_state.stocks.append({'w': 36.0, 'h': 72.0}))

    st.title("🖼️ GlaCal Master: ระบบล็อคการใช้แผ่นใหญ่ก่อนเสมอ")
    st.info("💡 ระบบจะจัดลำดับความสำคัญโดยเลือกใช้กระจกแผ่นใหญ่ที่สุดในคลังก่อน หากชิ้นงานสามารถวางได้")

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

            c_btn1, _ = st.columns([0.15, 0.85])
            with c_btn1:
                if st.button("➕ เพิ่มชิ้นงาน", key=f"add_it_{p_idx}"):
                    proj['items'].append({'w': 10.0, 'h': 10.0, 'qty': 1});
                    st.rerun()

            if st.button(f"🚀 เริ่มคำนวณ (บังคับใช้แผ่นใหญ่)", key=f"calc_{p_idx}", type="primary"):
                stocks_data = st.session_state.stocks
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]

                results = run_simulation_big_first(stocks_data, pieces_data, allowance, trials=50)

                if results:
                    st.success(f"📊 ผลลัพธ์: ใช้กระจกทั้งหมด {len(results)} แผ่น")
                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['width']}x{s['height']}", expanded=True):
                                eff = (s['used_area'] / (s['width'] * s['height'])) * 100
                                st.write(f"📊 ประสิทธิภาพ: **{eff:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(s['width'] * s['height'] - s['used_area']):.2f}** ตร.นิ้ว")
                                st.progress(min(eff / 100, 1.0))
                                for p in s['rects']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
                else:
                    st.error("❌ ไม่สามารถคำนวณได้")
