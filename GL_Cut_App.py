import streamlit as st
from rectpack import newPacker
import rectpack.packer as packer

# --- 1. ระบบรหัสผ่าน ---
PASSWORD = "CK3006"


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 GlaCal Master (Pure Cut)")
        pwd = st.text_input("กรุณาใส่รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ รหัสผ่านไม่ถูกต้อง")
        return False
    return True


# --- 2. ฟังก์ชันคำนวณ (ลองทุกแผ่นในสต็อก - ไม่เผื่อรอยตัด) ---
def calculate_pure_mix(stocks, pieces):
    # เรียงชิ้นงานจากพื้นที่มากไปน้อย
    remaining_pieces = sorted(pieces, key=lambda x: x['w'] * x['h'], reverse=True)
    results = []

    while remaining_pieces:
        best_sheet = None
        best_packed_indices = []
        max_used_area = -1

        # วนลูปทดสอบแผ่นสต็อกทุกขนาดที่มี
        for s_idx, s_item in enumerate(stocks):
            # ลองทั้งแนวตั้งและแนวนอนของแผ่นกระจก
            for sw, sh in [(s_item['w'], s_item['h']), (s_item['h'], s_item['w'])]:
                temp_packer = newPacker(rotation=True)
                temp_packer.add_bin(sw, sh)

                for i, p in enumerate(remaining_pieces):
                    temp_packer.add_rect(p['w'], p['h'], rid=i)

                temp_packer.pack()

                # ตรวจสอบผลการยัดงานในแผ่นทดลองนี้
                if len(temp_packer) > 0:
                    b = temp_packer[0]
                    current_used_area = sum(r.width * r.height for r in b)

                    # ถ้าแผ่นไซส์นี้ยัดงานได้พื้นที่คุ้มกว่าเดิม ให้บันทึกไว้
                    if current_used_area > max_used_area:
                        max_used_area = current_used_area
                        best_packed_indices = [r.rid for r in b]
                        best_sheet = {
                            'sw': sw, 'sh': sh,
                            'used_area': current_used_area,
                            'rects': [{'w': r.width, 'h': r.height} for r in b]
                        }

        if not best_sheet or not best_packed_indices:
            break  # ชิ้นงานที่เหลือใหญ่เกินแผ่นสต็อกทุกแผ่น

        results.append(best_sheet)

        # ลบชิ้นงานที่วางไปแล้วออกจากรายการรอตัด
        for idx in sorted(best_packed_indices, reverse=True):
            remaining_pieces.pop(idx)

    return results, remaining_pieces


# --- 3. UI ---
st.set_page_config(page_title="GlaCal Pure Pro", layout="wide")

if check_password():
    # เตรียมข้อมูลตั้งต้น
    if 'stocks' not in st.session_state:
        st.session_state.stocks = [{'w': 48.0, 'h': 96.0}]
    if 'projects' not in st.session_state:
        st.session_state.projects = [{'name': 'ชุดงานที่ 1', 'items': [{'w': 20.0, 'h': 20.0, 'qty': 5}]}]

    # --- Sidebar: จัดการสต็อก ---
    with st.sidebar:
        st.title("📦 คลังกระจก (Stock)")
        st.caption("หน่วยวัด: นิ้ว")
        for si, s in enumerate(st.session_state.stocks):
            with st.container(border=True):
                c1, c2, c3 = st.columns([0.4, 0.4, 0.2])
                s['w'] = c1.number_input(f"กว้าง", value=float(s['w']), key=f"sw_{si}")
                s['h'] = c2.number_input(f"สูง", value=float(s['h']), key=f"sh_{si}")
                if c3.button("❌", key=f"del_s_{si}"):
                    st.session_state.stocks.pop(si);
                    st.rerun()
        st.button("➕ เพิ่มขนาดคลัง", on_click=lambda: st.session_state.stocks.append({'w': 36.0, 'h': 72.0}))

    # --- Main: จัดการชิ้นงาน ---
    st.title("🖼️ GlaCal: คำนวณตัดกระจก (Pure Efficiency)")
    st.info("💡 ระบบจะเลือกแผ่นจากคลังที่ยัดชิ้นงานได้แน่นที่สุดทีละแผ่น โดยไม่คิดรอยตัด")

    for p_idx, proj in enumerate(st.session_state.projects):
        with st.container(border=True):
            proj['name'] = st.text_input("ชื่อโปรเจกต์", value=proj['name'], key=f"pname_{p_idx}")
            st.write("📝 **รายการชิ้นงาน (กว้าง x สูง)**")

            for i, it in enumerate(proj['items']):
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([0.35, 0.35, 0.2, 0.1])
                    it['w'] = c1.number_input(f"กว้าง", value=float(it['w']), key=f"w_{p_idx}_{i}")
                    it['h'] = c2.number_input(f"สูง", value=float(it['h']), key=f"h_{p_idx}_{i}")
                    it['qty'] = c3.number_input(f"จำนวน", value=int(it['qty']), min_value=1, key=f"q_{p_idx}_{i}")
                    if c4.button("❌", key=f"del_it_{p_idx}_{i}"):
                        proj['items'].pop(i);
                        st.rerun()

            col_a, col_b = st.columns([0.15, 0.85])
            with col_a:
                if st.button("➕ เพิ่มชิ้นงาน", key=f"add_it_{p_idx}"):
                    proj['items'].append({'w': 10.0, 'h': 10.0, 'qty': 1});
                    st.rerun()

            if st.button(f"🚀 คำนวณ (ประหยัดแผ่นสูงสุด)", key=f"calc_{p_idx}", type="primary"):
                pieces_data = [{'w': it['w'], 'h': it['h']} for it in proj['items'] for _ in range(int(it['qty']))]

                results, rem = calculate_pure_mix(st.session_state.stocks, pieces_data)

                if results:
                    st.success(f"📊 สรุป: ใช้กระจกทั้งหมด {len(results)} แผ่น")
                    res_grid = st.columns(3)
                    for idx, s in enumerate(results):
                        with res_grid[idx % 3]:
                            with st.expander(f"แผ่นที่ {idx + 1}: {s['sw']}x{s['sh']}", expanded=True):
                                area = s['sw'] * s['sh']
                                eff = (s['used_area'] / area) * 100
                                st.write(f"📊 ประสิทธิภาพ: **{eff:.1f}%**")
                                st.write(f"♻️ เศษเหลือ: **{(area - s['used_area']):.2f}** ตร.นิ้ว")
                                st.progress(min(eff / 100, 1.0))
                                for p in s['rects']:
                                    st.code(f"✂️ {p['w']} x {p['h']} นิ้ว")
                    if rem:
                        st.error(f"⚠️ เหลือ {len(rem)} ชิ้นที่ใหญ่เกินกว่ากระจกในสต็อก")
                else:
                    st.error("❌ ไม่สามารถคำนวณได้ ตรวจสอบข้อมูลชิ้นงานและสต็อก")
