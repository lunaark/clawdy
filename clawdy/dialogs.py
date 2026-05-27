"""像素风对话框 UI 组件 + 打卡弹窗"""

import tkinter as tk
from datetime import date

from .constants import (
    _ZH, FPS,
    PX_BG, PX_BG_SOFT, PX_BORDER, PX_BORDER_SOFT,
    PX_ACCENT, PX_ACCENT_DARK, PX_TEXT, PX_TEXT_SOFT,
    PX_INPUT_BG, PX_DANGER, PX_SUCCESS, PX_GOLD,
    PX_FONT, PX_FONT_B, PX_FONT_TITLE,
)


# ─── 通用 UI 组件 ────────────────────────────────────────────

def pixel_frame(parent, bg=PX_BG):
    outer = tk.Frame(parent, bg=PX_BORDER, bd=0)
    mid = tk.Frame(outer, bg=PX_BORDER_SOFT, bd=0)
    mid.pack(padx=2, pady=2, fill='both', expand=True)
    inner = tk.Frame(mid, bg=bg, bd=0)
    inner.pack(padx=2, pady=2, fill='both', expand=True)
    return outer, inner


def pixel_entry(parent, var, width=None):
    wrap = tk.Frame(parent, bg=PX_BORDER_SOFT)
    entry = tk.Entry(
        wrap, textvariable=var, font=PX_FONT,
        bg=PX_INPUT_BG, fg=PX_TEXT,
        insertbackground=PX_TEXT,
        relief='flat', bd=0, highlightthickness=0,
    )
    if width:
        entry.config(width=width)
    entry.pack(padx=2, pady=2, fill='x', ipady=4)
    return wrap, entry


def pixel_button(parent, text, command, primary=False, danger=False):
    if danger:
        fg, bg, border, hover = '#FFFFFF', PX_DANGER, PX_BORDER, '#A63A2A'
    elif primary:
        fg, bg, border, hover = '#FFFFFF', PX_ACCENT, PX_BORDER, PX_ACCENT_DARK
    else:
        fg, bg, border, hover = PX_TEXT, PX_BG_SOFT, PX_BORDER_SOFT, PX_BG
    wrap = tk.Frame(parent, bg=border)
    btn = tk.Label(
        wrap, text=text, font=PX_FONT_B, fg=fg, bg=bg,
        padx=12, pady=4, cursor='hand2',
    )
    btn.pack(padx=2, pady=2)
    btn.bind('<ButtonRelease-1>',
             lambda e: command() if 0 <= e.x <= btn.winfo_width()
             and 0 <= e.y <= btn.winfo_height() else None)
    btn.bind('<Enter>', lambda e: btn.config(bg=hover))
    btn.bind('<Leave>', lambda e: btn.config(bg=bg))
    return wrap


def bind_drag(dialog, handle):
    drag = {'x': 0, 'y': 0}
    def on_press(e):
        drag['x'] = e.x_root - dialog.winfo_x()
        drag['y'] = e.y_root - dialog.winfo_y()
    def on_drag(e):
        dialog.geometry(f'+{e.x_root - drag["x"]}+{e.y_root - drag["y"]}')
    handle.bind('<ButtonPress-1>', on_press)
    handle.bind('<B1-Motion>', on_drag)


def prep_dialog(pet, dialog):
    pet.root.wm_attributes('-topmost', False)
    dialog.wm_attributes('-topmost', True)
    dialog.config(bg=PX_BORDER)

    def _restore(e):
        if e.widget is dialog:
            try:
                pet.root.wm_attributes('-topmost', True)
            except Exception:
                pass
    dialog.bind('<Destroy>', _restore, add='+')


def _center_dialog(dialog, screen_w, screen_h, min_w=300):
    dialog.update_idletasks()
    dw = max(dialog.winfo_reqwidth(), min_w)
    dh = dialog.winfo_reqheight()
    x = (screen_w - dw) // 2
    y = (screen_h - dh) // 2
    dialog.geometry(f'{dw}x{dh}+{x}+{y}')


# ─── 打卡弹窗 ────────────────────────────────────────────────

def show_checkin_dialog(pet):
    if not pet.tracker.has_plan():
        show_new_plan_dialog(pet)
        return

    dialog = tk.Toplevel(pet.root)
    dialog.title('Clawdy')
    prep_dialog(pet, dialog)

    outer, frame = pixel_frame(dialog)
    outer.pack(fill='both', expand=True)
    frame.config(padx=18, pady=14)

    title_lbl = tk.Label(frame, text='🦀 ' + ('今日打卡' if _ZH else 'Today'),
                         font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
    title_lbl.pack(anchor='w', fill='x')

    list_frame = tk.Frame(frame, bg=PX_BG)
    list_frame.pack(fill='x', pady=(10, 0))

    def render_list():
        for w in list_frame.winfo_children():
            w.destroy()
        for pid, pname, pdone, ptotal in pet.tracker.plan_names():
            done_today = pet.tracker.checked_today(pid)
            completed = pdone >= ptotal
            card_border = tk.Frame(list_frame, bg=PX_BORDER_SOFT)
            card_border.pack(fill='x', pady=(0, 6))
            card = tk.Frame(card_border, bg=PX_BG_SOFT, padx=10, pady=8)
            card.pack(padx=2, pady=2, fill='x')

            info = tk.Frame(card, bg=PX_BG_SOFT)
            info.pack(side='left', fill='x', expand=True)
            pct = int(pdone / max(ptotal, 1) * 100)
            tk.Label(info, text=pname, font=PX_FONT_B,
                     fg=PX_TEXT, bg=PX_BG_SOFT, anchor='w').pack(anchor='w')
            tk.Label(info, text=f'{pdone}/{ptotal}  ({pct}%)',
                     font=PX_FONT, fg=PX_TEXT_SOFT,
                     bg=PX_BG_SOFT, anchor='w').pack(anchor='w')

            btn_box = tk.Frame(card, bg=PX_BG_SOFT)
            btn_box.pack(side='right')

            if completed:
                tk.Label(btn_box, text='✓ ' + ('已完成' if _ZH else 'Done'),
                         font=PX_FONT_B, fg=PX_GOLD,
                         bg=PX_BG_SOFT, padx=10).pack()
            elif done_today:
                tk.Label(btn_box, text='✓ ' + ('今日已打' if _ZH else 'Today ✓'),
                         font=PX_FONT_B, fg=PX_SUCCESS,
                         bg=PX_BG_SOFT, padx=10).pack()
            else:
                pixel_button(
                    btn_box, '打卡' if _ZH else 'Check',
                    lambda p=pid, n=pname: _checkin_with_note(
                        pet, p, n, on_done=render_list, parent=dialog),
                    primary=True,
                ).pack()

    render_list()

    btn_frame = tk.Frame(frame, bg=PX_BG)
    btn_frame.pack(fill='x', pady=(12, 0))
    pixel_button(btn_frame, '关闭' if _ZH else 'Close',
                 dialog.destroy).pack(side='right')

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, pet.screen_w, pet.screen_h, 340)
    bind_drag(dialog, title_lbl)
    dialog.lift()


def _checkin_with_note(pet, pid, plan_name, on_done=None, parent=None):
    dialog = tk.Toplevel(parent or pet.root)
    dialog.title('Clawdy')
    prep_dialog(pet, dialog)

    outer, frame = pixel_frame(dialog)
    outer.pack(fill='both', expand=True)
    frame.config(padx=16, pady=12)

    p = pet.tracker.plans.get(pid, {})
    count = len(p.get('records', [])) + 1
    title = f'🦀 {plan_name} · 第 {count} 次 ✅' if _ZH \
        else f'🦀 {plan_name} · #{count} ✅'
    title_lbl = tk.Label(frame, text=title, font=PX_FONT_TITLE,
                         fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
    title_lbl.pack(anchor='w', fill='x')

    tk.Label(frame, text='写一句话（可跳过）' if _ZH else 'Leave a note (optional)',
             font=PX_FONT, fg=PX_TEXT_SOFT, bg=PX_BG).pack(anchor='w', pady=(10, 2))
    note_var = tk.StringVar()
    wrap, entry = pixel_entry(frame, note_var)
    wrap.pack(fill='x')

    def do_submit():
        note = note_var.get().strip()
        total = p.get('total', 0)
        done_before = len(p.get('records', []))
        was_milestone = done_before in (
            round(total * 0.25),
            round(total * 0.50),
            round(total * 0.75),
        )
        pet.tracker.checkin_plan(pid, note)
        pet._update_mood()
        dialog.destroy()
        pet._checkin_celebrate_frames = FPS * 3
        pet.sm.force_state('celebrate', duration=3.0)
        done_after = done_before + 1
        if done_after >= total or was_milestone:
            pet.root.after(2000, pet._trigger_firework)
        if on_done:
            on_done()

    entry.bind('<Return>', lambda e: do_submit())
    dialog.bind('<Escape>', lambda e: dialog.destroy())

    btn_frame = tk.Frame(frame, bg=PX_BG)
    btn_frame.pack(fill='x', pady=(12, 0))
    pixel_button(btn_frame, '打卡！' if _ZH else 'Check In!',
                 do_submit, primary=True).pack(side='right')
    pixel_button(btn_frame, '取消' if _ZH else 'Cancel',
                 dialog.destroy).pack(side='right', padx=(0, 8))

    _center_dialog(dialog, pet.screen_w, pet.screen_h, 280)
    bind_drag(dialog, title_lbl)
    dialog.lift()
    dialog.after(50, lambda: entry.focus_force())


def show_progress_dialog(pet):
    if not pet.tracker.has_plan():
        show_manage_plans_dialog(pet)
        return

    dialog = tk.Toplevel(pet.root)
    dialog.title('Clawdy')
    prep_dialog(pet, dialog)

    outer, frame = pixel_frame(dialog)
    outer.pack(fill='both', expand=True)
    frame.config(padx=18, pady=14)

    title_lbl = tk.Label(
        frame, text='🦀 ' + ('全部进度' if _ZH else 'All Progress'),
        font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
    title_lbl.pack(anchor='w', fill='x')

    streak = pet.tracker.streak
    if streak > 0:
        streak_color = PX_DANGER if streak >= 7 else PX_ACCENT if streak >= 3 else PX_SUCCESS
        flame = '🔥' if streak >= 7 else '⚡' if streak >= 3 else '✨'
        streak_text = f'{flame} ' + (f'连续 {streak} 天' if _ZH else f'{streak} day streak')
        tk.Label(frame, text=streak_text, font=PX_FONT_B,
                 fg=streak_color, bg=PX_BG).pack(anchor='w', pady=(2, 0))

    list_frame = tk.Frame(frame, bg=PX_BG)
    list_frame.pack(fill='x', pady=(10, 0))

    def render_list():
        for w in list_frame.winfo_children():
            w.destroy()
        for pid, pname, pdone, ptotal in pet.tracker.plan_names():
            p = pet.tracker.plans.get(pid, {})
            progress = pdone / max(ptotal, 1)
            is_active = (pid == pet.tracker.active_id)

            card_border = tk.Frame(list_frame, bg=PX_BORDER_SOFT)
            card_border.pack(fill='x', pady=(0, 6))
            card = tk.Frame(card_border, bg=PX_BG_SOFT, padx=10, pady=8)
            card.pack(padx=2, pady=2, fill='x')

            top = tk.Frame(card, bg=PX_BG_SOFT)
            top.pack(fill='x')
            star = '★ ' if is_active else ''
            tk.Label(top, text=star + pname, font=PX_FONT_B,
                     fg=PX_ACCENT if is_active else PX_TEXT,
                     bg=PX_BG_SOFT, anchor='w').pack(side='left')
            tk.Label(top, text=f'{pdone}/{ptotal}  ({int(progress*100)}%)',
                     font=PX_FONT, fg=PX_TEXT_SOFT,
                     bg=PX_BG_SOFT).pack(side='right')

            bar_h = 10
            bar_border = tk.Frame(card, bg=PX_BORDER)
            bar_border.pack(fill='x', pady=(6, 0))
            bar_canvas = tk.Canvas(bar_border, height=bar_h, bg=PX_INPUT_BG,
                                   highlightthickness=0, bd=0)
            bar_canvas.pack(padx=2, pady=2, fill='x')

            def _paint_bar(cv=bar_canvas, prog=progress):
                cv.delete('all')
                bw = cv.winfo_width() or 240
                fw = int(bw * min(prog, 1.0))
                fc = PX_GOLD if prog >= 1.0 else PX_ACCENT
                if fw > 0:
                    cv.create_rectangle(0, 0, fw, bar_h, fill=fc, outline='')
                for i in range(1, 10):
                    gx = int(bw * i / 10)
                    cv.create_rectangle(gx, 0, gx + 1, bar_h,
                                        fill=PX_BORDER_SOFT, outline='')
            bar_canvas.bind('<Configure>', lambda e, fn=_paint_bar: fn())

            reward = p.get('reward', '')
            if reward:
                tk.Label(card, text='🎁 ' + reward, font=PX_FONT,
                         fg=PX_GOLD, bg=PX_BG_SOFT,
                         anchor='w').pack(anchor='w', pady=(6, 0))

            if p.get('records'):
                foot = tk.Frame(card, bg=PX_BG_SOFT)
                foot.pack(fill='x', pady=(6, 0))
                last = p['records'][-1]
                last_txt = ('最近 ' if _ZH else 'Last ') + last['date']
                if last.get('note'):
                    last_txt += f'  "{last["note"]}"'
                tk.Label(foot, text=last_txt, font=PX_FONT,
                         fg=PX_TEXT_SOFT, bg=PX_BG_SOFT,
                         anchor='w', wraplength=260,
                         justify='left').pack(side='left', fill='x',
                                              expand=True)
                pixel_button(
                    foot, '↩ ' + ('撤销' if _ZH else 'Undo'),
                    lambda p=pid: _undo_plan(pet, p, on_done=render_list,
                                             parent=dialog),
                ).pack(side='right')

    render_list()

    tk.Frame(frame, bg=PX_BORDER_SOFT, height=1).pack(fill='x', pady=(12, 8))
    btn_frame = tk.Frame(frame, bg=PX_BG)
    btn_frame.pack(fill='x')
    pixel_button(btn_frame, '关闭' if _ZH else 'Close',
                 dialog.destroy, primary=True).pack(side='right')
    pixel_button(btn_frame, '打卡' if _ZH else 'Check In',
                 lambda: (dialog.destroy(),
                          pet.root.after(80, lambda: show_checkin_dialog(pet)))).pack(
                              side='right', padx=(0, 8))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, pet.screen_w, pet.screen_h, 340)
    bind_drag(dialog, title_lbl)
    dialog.lift()


def _undo_plan(pet, pid, on_done=None, parent=None):
    p = pet.tracker.plans.get(pid)
    if not p or not p.get('records'):
        return
    last = p['records'][-1]
    confirm = tk.Toplevel(parent or pet.root)
    confirm.title('Clawdy')
    prep_dialog(pet, confirm)
    c_outer, cf = pixel_frame(confirm)
    c_outer.pack(fill='both', expand=True)
    cf.config(padx=16, pady=12)
    txt = f'撤销「{p["name"]}」{last["date"]} 的打卡？' if _ZH \
        else f'Undo "{p["name"]}" on {last["date"]}?'
    if last.get('note'):
        txt += f'\n"{last["note"]}"'
    tk.Label(cf, text=txt, font=PX_FONT, fg=PX_TEXT, bg=PX_BG,
             wraplength=260, justify='center').pack(pady=(0, 10))
    cbf = tk.Frame(cf, bg=PX_BG)
    cbf.pack()

    def yes():
        p['records'].pop()
        pet.tracker._save()
        pet._update_mood()
        confirm.destroy()
        if on_done:
            on_done()

    pixel_button(cbf, '撤销' if _ZH else 'Undo',
                 yes, danger=True).pack(side='left', padx=4)
    pixel_button(cbf, '取消' if _ZH else 'Cancel',
                 confirm.destroy).pack(side='left', padx=4)
    _center_dialog(confirm, pet.screen_w, pet.screen_h, 280)
    confirm.lift()


def show_manage_plans_dialog(pet):
    plans = pet.tracker.plan_names()
    if not plans:
        show_new_plan_dialog(pet)
        return

    dialog = tk.Toplevel(pet.root)
    dialog.title('Clawdy')
    prep_dialog(pet, dialog)

    outer, frame = pixel_frame(dialog)
    outer.pack(fill='both', expand=True)
    frame.config(padx=18, pady=14)

    tk.Label(frame, text='🦀 ' + ('管理计划' if _ZH else 'Manage Plans'),
             font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG).pack(anchor='w')

    for pid, pname, pdone, ptotal in plans:
        is_active = pid == pet.tracker.active_id
        card_border = tk.Frame(frame, bg=PX_BORDER_SOFT)
        card_border.pack(fill='x', pady=(8, 0))
        card = tk.Frame(card_border, bg=PX_BG_SOFT, padx=10, pady=8)
        card.pack(padx=2, pady=2, fill='x')

        info = tk.Frame(card, bg=PX_BG_SOFT)
        info.pack(side='left', fill='x', expand=True)

        prefix = '▶ ' if is_active else '  '
        name_color = PX_ACCENT if is_active else PX_TEXT
        tk.Label(info, text=f'{prefix}{pname}',
                 font=PX_FONT_B, fg=name_color,
                 bg=PX_BG_SOFT, anchor='w').pack(anchor='w')
        pct = int(pdone / max(ptotal, 1) * 100)
        tk.Label(info, text=f'{pdone}/{ptotal}  ({pct}%)',
                 font=PX_FONT, fg=PX_TEXT_SOFT,
                 bg=PX_BG_SOFT, anchor='w').pack(anchor='w')

        btns = tk.Frame(card, bg=PX_BG_SOFT)
        btns.pack(side='right')

        if not is_active:
            pixel_button(btns, '切换' if _ZH else 'Use',
                         lambda p=pid: (
                             pet.tracker.switch_plan(p),
                             pet._update_mood(),
                             dialog.destroy(),
                             pet.root.after(100, lambda: show_manage_plans_dialog(pet)),
                         )).pack(side='left', padx=2)

        pixel_button(btns, '删除' if _ZH else 'Del',
                     lambda p=pid, n=pname: _confirm_delete_plan(
                         pet, p, n, dialog,
                     ), danger=True).pack(side='left', padx=2)

    tk.Frame(frame, bg=PX_BORDER_SOFT, height=1).pack(fill='x', pady=(12, 8))
    btn_frame = tk.Frame(frame, bg=PX_BG)
    btn_frame.pack(fill='x')

    pixel_button(btn_frame, '关闭' if _ZH else 'Close',
                 dialog.destroy, primary=True).pack(side='right')

    pixel_button(btn_frame, '+ ' + ('新建计划' if _ZH else 'New Plan'),
                 lambda: (dialog.destroy(), show_new_plan_dialog(pet))
                 ).pack(side='left')

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, pet.screen_w, pet.screen_h, 320)
    dialog.lift()


def _confirm_delete_plan(pet, pid, name, parent_dialog):
    confirm = tk.Toplevel(parent_dialog)
    confirm.title('Clawdy')
    prep_dialog(pet, confirm)

    c_outer, cf = pixel_frame(confirm)
    c_outer.pack(fill='both', expand=True)
    cf.config(padx=16, pady=12)

    txt = f'确定删除「{name}」？\n所有打卡记录将丢失！' if _ZH else f'Delete "{name}"?\nAll records will be lost!'
    tk.Label(cf, text=txt, font=PX_FONT, fg=PX_TEXT, bg=PX_BG,
             wraplength=240, justify='center').pack(pady=(0, 10))

    cbf = tk.Frame(cf, bg=PX_BG)
    cbf.pack()

    def yes():
        pet.tracker.delete_plan(pid)
        pet._update_mood()
        confirm.destroy()
        parent_dialog.destroy()
        if pet.tracker.plan_names():
            pet.root.after(100, lambda: show_manage_plans_dialog(pet))

    pixel_button(cbf, '删除' if _ZH else 'Delete',
                 yes, danger=True).pack(side='left', padx=4)
    pixel_button(cbf, '取消' if _ZH else 'Cancel',
                 confirm.destroy).pack(side='left', padx=4)

    _center_dialog(confirm, pet.screen_w, pet.screen_h, 280)
    confirm.lift()


def show_new_plan_dialog(pet):
    dialog = tk.Toplevel(pet.root)
    dialog.title('Clawdy')
    prep_dialog(pet, dialog)

    outer, frame = pixel_frame(dialog)
    outer.pack(padx=0, pady=0, fill='both', expand=True)
    frame.config(padx=18, pady=14)

    title_lbl = tk.Label(frame, text='🦀 ' + ('新建打卡计划' if _ZH else 'New Plan'),
                         font=PX_FONT_TITLE, fg=PX_ACCENT, bg=PX_BG, cursor='fleur')
    title_lbl.pack(anchor='w', fill='x')

    def add_field(label_text, var):
        tk.Label(frame, text=label_text, font=PX_FONT,
                 fg=PX_TEXT_SOFT, bg=PX_BG, anchor='w').pack(fill='x', pady=(10, 2))
        wrap, entry = pixel_entry(frame, var)
        wrap.pack(fill='x')
        return entry

    name_var = tk.StringVar()
    name_entry = add_field('计划名称' if _ZH else 'Plan name', name_var)

    total_var = tk.StringVar(value='32')
    add_field('目标次数' if _ZH else 'Target count', total_var)

    reward_var = tk.StringVar()
    add_field(('完成奖励（选填）' if _ZH else 'Reward (optional)'), reward_var)

    date_var = tk.StringVar(value=date.today().isoformat())
    add_field('开始日期' if _ZH else 'Start date', date_var)

    def on_create():
        name = name_var.get().strip()
        if not name:
            return
        try:
            total = int(total_var.get().strip())
            if total <= 0:
                return
        except ValueError:
            return
        reward = reward_var.get().strip()
        start = date_var.get().strip()
        pet.tracker.create_plan(name, total, reward, start)
        pet._update_mood()
        dialog.destroy()

    dialog.bind('<Return>', lambda e: on_create())
    dialog.bind('<Escape>', lambda e: dialog.destroy())

    btn_frame = tk.Frame(frame, bg=PX_BG)
    btn_frame.pack(fill='x', pady=(16, 0))
    pixel_button(btn_frame, '创建' if _ZH else 'Create',
                 on_create, primary=True).pack(side='right')
    pixel_button(btn_frame, '取消' if _ZH else 'Cancel',
                 dialog.destroy).pack(side='right', padx=(0, 8))

    _center_dialog(dialog, pet.screen_w, pet.screen_h, 300)
    bind_drag(dialog, title_lbl)
    dialog.lift()
    dialog.after(50, lambda: name_entry.focus_force())
