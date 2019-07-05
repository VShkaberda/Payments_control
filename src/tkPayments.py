# -*- coding: utf-8 -*-
"""
Created on Wed May 15 22:51:04 2019

@author: v.shkaberda
"""
from calendar import month_name
from datetime import datetime
from decimal import Decimal
from tkcalendar import DateEntry
from tkinter import ttk, messagebox
from math import ceil
from xl import export_to_excel
import locale
import tkinter as tk

# example of subsription and default recipient
EMAIL_TO = b'\xd0\xa4\xd0\xbe\xd0\xb7\xd0\xb7\xd0\xb8|\
\xd0\x9b\xd0\xbe\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd0\xb8\xd0\xba\xd0\xb0|\
\xd0\x90\xd0\xbd\xd0\xb0\xd0\xbb\xd0\xb8\xd1\x82\xd0\xb8\xd0\xba\xd0\xb8'.decode()


class AccessError(tk.Tk):
    """ Raise an error when user doesn't have permission to work with app.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showerror(
            'Ошибка доступа',
            'Нет прав для работы с приложением.\n'
            'Для получения прав обратитесь на рассылку ' + EMAIL_TO
        )
        self.destroy()


class LoginError(tk.Tk):
    """ Raise an error when user doesn't have permission to work with db.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showerror(
                'Ошибка подключения',
                'Нет прав для работы с сервером.\n'
                'Обратитесь на рассылку ' + EMAIL_TO
        )
        self.destroy()


class NetworkError(tk.Tk):
    """ Raise a message about network error.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showerror(
                'Ошибка cети',
                'Возникла общая ошибка сети.\nПерезапустите приложение'
        )
        self.destroy()


class StringSumVar(tk.StringVar):
    """ Contains function that returns var formatted in a such way, that
    it can be converted into a float without an error"""
    def get_float_form(self, *args, **kwargs):
        return super().get(*args, **kwargs).replace(' ', '').replace(',', '.')


class PaymentApp(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__()
        self.title('Заявки на оплату')
        self.iconbitmap('../resources/payment.ico')
        # geometry_storage {Framename:(width, height)}
        self._geometry = {'PreviewForm': (1200, 600),
                          'CreateForm': (750, 400)}
        # Virtual event for creating request
        self.event_add("<<create>>", "<Control-S>", "<Control-s>",
                       "<Control-Ucircumflex>", "<Control-ucircumflex>",
                       "<Control-twosuperior>", "<Control-threesuperior>",
                       "<KeyPress-F5>")
        self.bind("<<create>>", self._create_request)
        self.active_frame = None
        # handle the window close event
        self.protocol("WM_DELETE_WINDOW", self._quit)
        # hide until all frames have been created
        self.withdraw()
        # To import months names in cyrillic
        locale.setlocale(locale.LC_ALL, 'RU')
        # Customize header style (used in PreviewForm)
        style = ttk.Style()
        try:
            style.element_create("HeaderStyle.Treeheading.border", "from", "default")
            style.layout("HeaderStyle.Treeview.Heading", [
                ("HeaderStyle.Treeheading.cell", {'sticky': 'nswe'}),
                ("HeaderStyle.Treeheading.border", {'sticky': 'nswe', 'children': [
                    ("HeaderStyle.Treeheading.padding", {'sticky': 'nswe', 'children': [
                        ("HeaderStyle.Treeheading.image", {'side': 'right', 'sticky':''}),
                        ("HeaderStyle.Treeheading.text", {'sticky': 'we'})
                    ]})
                ]}),
            ])
            style.configure("HeaderStyle.Treeview.Heading",
                background="#eaeaea", foreground="black", relief='groove', font=('Calibri', 10))
            style.map("HeaderStyle.Treeview.Heading",
                      relief=[('active', 'sunken'), ('pressed', 'flat')])

            style.map('ButtonGreen.TButton')
            style.configure('ButtonGreen.TButton', foreground='green')

            style.map('ButtonRed.TButton')
            style.configure('ButtonRed.TButton', foreground='red')

            style.map('ButtonMenu.TButton')
            style.configure('ButtonMenu.TButton',
                            font=('Calibri', 16),
                            borderwidth='4')

            style.configure("Big.TLabelframe.Label", font=("Calibri", 14))
            style.configure("TMenubutton", background='white')
        except tk.TclError:
            # if during debug previous tk wasn't destroyed
            # and style remains modified
            pass

        # the container is where we'll stack a bunch of frames
        # the one we want to be visible will be raised above others
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._frames = {}
        for F in (PreviewForm, CreateForm):
            frame_name = F.__name__
            frame = F(parent=container, controller=self, **kwargs)
            self._frames[frame_name] = frame
            # put all of them in the same location
            frame.grid(row=0, column=0, sticky='nsew')

        self._show_frame('PreviewForm')
        # restore after withdraw
        self.deiconify()

    def _center_window(self, w, h):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        start_x = int((screen_width/2) - (w/2))
        start_y = int((screen_height/2) - (h/2))

        self.geometry('{}x{}+{}+{}'.format(w, h, start_x, start_y))

    def _fill_CreateForm(self, МВЗ, Офис, Контрагент, **kwargs):
        frame = self._frames['CreateForm']
        frame._fill_from_PreviewForm(МВЗ, Офис, Контрагент)

    def _show_frame(self, frame_name):
        """ Show a frame for the given frame name
        """
        if frame_name == 'CreateForm':
            self.resizable(width=False, height=False)
        else:
            self.resizable(width=True, height=True)
        frame = self._frames[frame_name]
        frame.tkraise()
        self._center_window(*(self._geometry[frame_name]))
        # Make sure active_frame changes in case of network error
        try:
            if frame_name in ('PreviewForm'):
                frame._resize_columns()
                frame._refresh()
        finally:
            self.active_frame = frame_name

    def _create_request(self, event):
        "Draws an orange blob in self.canv where the mouse is."
        if self.active_frame == 'CreateForm':
            self._frames[self.active_frame]._create_request()

    def _quit(self):
        if self.active_frame != 'PreviewForm':
            self._show_frame('PreviewForm')
        elif messagebox.askokcancel("Выход", "Выйти из приложения?"):
            self.destroy()


class PaymentFrame(tk.Frame):
    def __init__(self, parent, controller, connection, user_info):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.conn = connection
        self.user_info = user_info
        # Often used info
        self.userID = user_info.UserID

    def _add_user_label(self, parent):
        user_label = tk.Label(parent, text=self.user_info.ShortUserName, padx=10)
        user_label.pack(side=tk.RIGHT, anchor=tk.NE)

    def _format_float(self, sum_float):
        return '{:,.2f}'.format(sum_float).replace(',', ' ').replace('.', ',')

    def _on_focus_in_format_sum(self, event):
        varname = str(event.widget.cget("textvariable"))
        sum_entry = event.widget.get().replace(' ', '')
        event.widget.setvar(varname, sum_entry)

    def _on_focus_out_format_sum(self, event):
        """ Function to be bind to focus out of self.sum_entry"""
        if not event.widget.get().replace(',', '.'):
            return
        sum_entry = float(event.widget.get().replace(',', '.'))
        varname = str(event.widget.cget("textvariable"))
        event.widget.setvar(varname, self._format_float(sum_entry))

    def _validate_sum(self, sum_entry):
        """ Validation of self.sum_entry"""
        sum_entry = sum_entry.replace(',', '.').replace(' ', '')
        try:
            if not sum_entry or 0 <= float(sum_entry) < 10**9:
                return True
        except (TypeError, ValueError):
            return False
        return False


class CreateForm(PaymentFrame):
    def __init__(self, parent, controller, connection, user_info,
                 mvz, **kwargs):
        super().__init__(parent, controller, connection, user_info)
        # {mvzSAP: [mvzname, [office1, office2, ...]], ...}
        self.mvz = {}
        for mvzSAP, mvzname, office in mvz:
            try:
                self.mvz[mvzname][1].append(office)
            except KeyError:
                self.mvz[mvzname] = [mvzSAP, [office]]

        # Top Frame with description and user name
        top = tk.Frame(self, name='top_cf', padx=5)

        main_label = tk.Label(top, text='Форма создания заявки на согласование',
                              padx=10, font=('Calibri', 10, 'bold'))
        main_label.pack(side=tk.LEFT, expand=False, anchor=tk.NW)

        self._add_user_label(top)

        # First Fill Frame with (MVZ, office)
        row1_cf = tk.Frame(self, name='row1_cf', padx=15)

        self.mvz_label = tk.Label(row1_cf, text='МВЗ', padx=10)
        self.mvz_current = tk.StringVar()
        #self.mvz_current.set(self.mvznames[0]) # default value
        self.mvz_box = ttk.OptionMenu(row1_cf, self.mvz_current, '', *self.mvz.keys(),
                                      command = self._choose_mvz)
        self.mvz_box.config(width=40)
#        self.mvz_box = ttk.Combobox(row1_cf, width=35)
#        self.mvz_box['values'] = self.mvznames
#        self.mvz_box.bind("<<ComboboxSelected>>", self._choose_mvz)
        self.mvz_sap = tk.Label(row1_cf, padx=6, bg='lightgray', width=11)
        self.office_label = tk.Label(row1_cf, text='Офис', padx=10)
        self.office_box = ttk.Combobox(row1_cf, width=20, state='disabled')
        #self.office_box['values'] = self.mvzSAP
        #self.office_box['values'] = list(self.mvz.keys())

        # Pack row1_cf
        self._row1_pack()

        # Second Fill Frame with (contragent, CSP)
        row2_cf = tk.Frame(self, name='row2_cf', padx=15)

        self.contragent_label = tk.Label(row2_cf, text='Контрагент', padx=10)
        self.contragent_entry = tk.Entry(row2_cf, width=30)
        self.csp = tk.Label(row2_cf, text='CSP', padx=10)
        self.csp_entry = tk.Entry(row2_cf, width=60)

        # Pack row2_cf
        self._row2_pack()

        # Second Fill Frame with (Plan date, Sum, Tax)
        row3_cf = tk.Frame(self, name='row3_cf', padx=15)

        self.plan_date_label = tk.Label(row3_cf, text='Плановая дата', padx=10)
        self.plan_date_entry = DateEntry(row3_cf, width=12, state='readonly',
                    font=('Calibri', 10), selectmode='day', borderwidth=2)
        self.sum_label = tk.Label(row3_cf, text='Сумма без НДС', padx=20)
        self.sumtotal = StringSumVar()
        self.sumtotal.set('0,00')
        vcmd = (self.register(self._validate_sum))
        self.sum_entry = tk.Entry(row3_cf, name='sum_entry', width=20,
                                  textvariable=self.sumtotal, validate='all',
                                  validatecommand=(vcmd, '%P')
                                  )
        self.sum_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_entry.bind("<FocusOut>", self._on_focus_out_format_sum)
        self.nds_label = tk.Label(row3_cf, text='НДС', padx=20)
        self.nds = tk.IntVar()
        self.nds.set(20)
        self.nds20 = ttk.Radiobutton(row3_cf, text="20 %", variable=self.nds, value=20)
        self.nds7 = ttk.Radiobutton(row3_cf, text="7 %", variable=self.nds, value=7)
        self.nds0 = ttk.Radiobutton(row3_cf, text="0 %", variable=self.nds, value=0)

        # Pack row3_cf
        self._row3_pack()

        # Text Frame
        text_cf = ttk.LabelFrame(self, text=' Описание заявки ', name='text_cf')

        self.desc_text = tk.Text(text_cf)    # input and output box
        self.desc_text.pack(in_=text_cf, expand=True, pady=15)

        # Bottom Frame with buttons
        bottom_cf = tk.Frame(self, name='bottom_cf')

        bt3 = ttk.Button(bottom_cf, text="Назад", width=10,
                         command=lambda: controller._show_frame('PreviewForm'))
        bt3.pack(side=tk.RIGHT, padx=15, pady=10)

        bt2 = ttk.Button(bottom_cf, text="Очистить", width=10,
                         command=self._clear, style='ButtonRed.TButton')
        bt2.pack(side=tk.RIGHT, padx=15, pady=10)

        bt1 = ttk.Button(bottom_cf, text="Создать", width=10,
                         command=self._create_request, style='ButtonGreen.TButton')
        bt1.pack(side=tk.RIGHT, padx=15, pady=10)

        # Pack frames
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        bottom_cf.pack(side=tk.BOTTOM, fill=tk.X)
        row1_cf.pack(side=tk.TOP, fill=tk.X)
        row2_cf.pack(side=tk.TOP, fill=tk.X)
        row3_cf.pack(side=tk.TOP, fill=tk.X)
        text_cf.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)

    def _choose_mvz(self, event):
        self.mvz_sap.config(text=self.mvz[self.mvz_current.get()][0])
        offices = self.mvz[self.mvz_current.get()][1]
        if len(offices) == 1:
            self.office_box.set(offices[0])
            self.office_box.configure(state="disabled")
        else:
            self.office_box.set('')
            self.office_box['values'] = offices
            self.office_box.configure(state="readonly")

    def _clear(self):
        #self.mvz_box.set('')
        self.mvz_current.set('')
        self.mvz_sap.config(text='')
        self.office_box.set('')
        self.office_box.configure(state="disabled")
        self.contragent_entry.delete(0, tk.END)
        self.csp_entry.delete(0, tk.END)
        self.plan_date_entry.delete(0, tk.END)
        self.sumtotal.set('0,00')
        self.nds.set(20)
        self.desc_text.delete("1.0", tk.END)
        self.plan_date_entry.set_date(datetime.now())

    def _create_request(self):
        messagetitle = 'Создание заявки'
        if not self.mvz_current.get():
            messagebox.showerror(
                    messagetitle, 'Не указано МВЗ'
            )
            return
        if not self._validate_plan_date():
            messagebox.showerror(
                    messagetitle,
                    'Плановая дата не может быть сегодняшней или ранее'
            )
            return
        if not self.office_box.get():
            messagebox.showerror(
                    messagetitle, 'Не выбран офис'
            )
            return
        request = {'mvz': self.mvz_sap.cget('text'),
                   'office': self.office_box.get(),
                   'contragent': self.contragent_entry.get() or None,
                   'csp': self.csp_entry.get() or None,
                   'plan_date': self.plan_date_entry.get(),
                   'sumtotal': float(self.sumtotal.get_float_form()
                                     if self.sum_entry.get() else 0),
                   'nds':  self.nds.get(),
                   'text': self.desc_text.get("1.0", tk.END)
                   }
        created_success = self.conn.create_request(userID=self.userID, **request)
        if created_success:
            messagebox.showinfo(
                    messagetitle, 'Заявка создана'
            )
            self._clear()
            self.controller._show_frame('PreviewForm')
        else:
            messagebox.showerror(
                    messagetitle, 'Произошла ошибка при создании заявки'
            )

    def _fill_from_PreviewForm(self, mvz, office, contragent):
        """ When button "Создать из заявки" from PreviewForm is activated,
        fill some fields taken from choosed in PreviewForm request.
        """
        self.mvz_current.set(mvz)
        self.mvz_sap.config(text=self.mvz[self.mvz_current.get()][0])
        self.office_box.set(office)
        self.contragent_entry.delete(0, tk.END)
        self.contragent_entry.insert(0, contragent)

    def _row1_pack(self):
        self.mvz_label.pack(side=tk.LEFT, pady=5)
        self.mvz_box.pack(side=tk.LEFT, padx=5, pady=5)
        self.mvz_sap.pack(side=tk.LEFT, pady=5)
        self.office_box.pack(side=tk.RIGHT, padx=5, pady=5)
        self.office_label.pack(side=tk.RIGHT, pady=5)

    def _row2_pack(self):
        self.contragent_label.pack(side=tk.LEFT, pady=5)
        self.contragent_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.csp_entry.pack(side=tk.RIGHT, padx=5, pady=5)
        self.csp.pack(side=tk.RIGHT, pady=5)

    def _row3_pack(self):
        self.plan_date_label.pack(side=tk.LEFT)
        self.plan_date_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.nds0.pack(side=tk.RIGHT, padx=7)
        self.nds7.pack(side=tk.RIGHT, padx=7)
        self.nds20.pack(side=tk.RIGHT, padx=8)
        self.nds_label.pack(side=tk.RIGHT, padx=5)
        self.sum_entry.pack(side=tk.RIGHT, padx=5, pady=5)
        self.sum_label.pack(side=tk.RIGHT)

    def _validate_plan_date(self):
        date = self.plan_date_entry.get()
        try:
            date = datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            date = datetime.strptime(date, '%d.%m.%y')
        today = datetime.now()
        return date > today


class PreviewForm(PaymentFrame):
    def __init__(self, parent, controller, connection, user_info, mvz,
                 allowed_initiators, **kwargs):
        super().__init__(parent, controller, connection, user_info)
        self.mvznames, self.mvzSAP, self.office = zip(*[('Все', None, 'Все'),] + mvz)
        self.office = tuple(sorted(set(self.office),
                                   key=lambda s: '' if s == 'Все' else s))
        self.initiatorsID, self.initiators = zip(*allowed_initiators)
        # Selectmode for treeview
        self.selectmode = 'extended' if user_info.isSuperUser else 'browse'
        # Parameters for sorting
        self.rows = None  # store all rows for sorting and redrawing
        self.sort_reversed_index = None  # reverse sorting for last sorted column
        self.month = list(month_name)
        # Virtual event for treeview
        self.event_add("<<select_all>>", "<Control-A>", "<Control-a>",
                       "<Control-ocircumflex>", "<Control-Ocircumflex>")

        # Top Frame with description and user name
        top = tk.Frame(self, name='top_cf', padx=5)

        main_label = tk.Label(top, text='Просмотр заявок',
                              padx=10, font=('Calibri', 10, 'bold'))
        main_label.pack(side=tk.LEFT, expand=False, anchor=tk.NW)

        self._add_user_label(top)

        top.pack(side=tk.TOP, fill=tk.X, expand=False)

        # Filters
        filterframe = ttk.LabelFrame(self, text=' Фильтры ', name='filterframe')

        # First Filter Frame with (MVZ, office)
        row1_cf = tk.Frame(filterframe, name='row1_cf', padx=15)

        self.initiator_label = tk.Label(row1_cf, text='Инициатор', padx=10)
        self.initiator_box = ttk.Combobox(row1_cf, width=35, state='readonly')
        self.initiator_box['values'] = self.initiators

        self.mvz_label = tk.Label(row1_cf, text='МВЗ', padx=10)
        self.mvz_box = ttk.Combobox(row1_cf, width=35, state='readonly')
        self.mvz_box['values'] = self.mvznames

        self.office_label = tk.Label(row1_cf, text='Офис', padx=20)
        self.office_box = ttk.Combobox(row1_cf, width=20, state='readonly')
        self.office_box['values'] = self.office

        # Pack row1_cf
        self._row1_pack()
        row1_cf.pack(side=tk.TOP, fill=tk.X)

        # Second Fill Frame with (Plan date, Sum, Tax)
        row2_cf = tk.Frame(filterframe, name='row2_cf', padx=15)

        self.plan_date_label_m = tk.Label(row2_cf, text='Плановая дата:  месяц', padx=10)
        self.plan_date_entry_m = ttk.Combobox(row2_cf, width=15, state='readonly')
        self.plan_date_entry_m['values'] = self.month
        self.plan_date_label_y = tk.Label(row2_cf, text='год', padx=20)
        self.year = tk.IntVar()
        self.plan_date_entry_y = tk.Spinbox(row2_cf, width=7, from_=2019, to=2029,
                                            font=('Calibri', 11), textvariable=self.year)
        self.sum_label_from = tk.Label(row2_cf, text='Сумма без НДС: от')
        self.sumtotal_from = StringSumVar()
        vcmd = (self.register(self._validate_sum))
        self.sum_entry_from = tk.Entry(row2_cf, width=12, textvariable=self.sumtotal_from,
                        validate='all', validatecommand=(vcmd, '%P')
                        )
        self.sum_entry_from.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_entry_from.bind("<FocusOut>", self._on_focus_out_format_sum)
        self.sum_label_to = tk.Label(row2_cf, text='до')
        self.sumtotal_to = StringSumVar()
        self.sum_entry_to = tk.Entry(row2_cf, width=12, textvariable=self.sumtotal_to,
                        validate='all', validatecommand=(vcmd, '%P'))
        self.sum_entry_to.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_entry_to.bind("<FocusOut>", self._on_focus_out_format_sum)
        self.nds_label = tk.Label(row2_cf, text='НДС', padx=20)
        self.nds = tk.IntVar()
        self.ndsall = ttk.Radiobutton(row2_cf, text="Любой", variable=self.nds, value=-1)
        self.nds20 = ttk.Radiobutton(row2_cf, text="20 %", variable=self.nds, value=20)
        self.nds7 = ttk.Radiobutton(row2_cf, text="7 %", variable=self.nds, value=7)
        self.nds0 = ttk.Radiobutton(row2_cf, text="0 %", variable=self.nds, value=0)

        # Pack row2_cf
        self._row2_pack()
        row2_cf.pack(side=tk.TOP, fill=tk.X)
        filterframe.pack(side=tk.TOP, fill=tk.X, expand=False, padx=10, pady=5)

        # Third Fill Frame (checkbox + button to apply filter)
        row3_cf = tk.Frame(filterframe, name='row3_cf', padx=15)

        self.show_for_approve = tk.IntVar()
        c = tk.Checkbutton(row3_cf, text="Показать заявки на утверждение (без фильтров)",
                           variable=self.show_for_approve)

        bt3_1 = ttk.Button(row3_cf, text="Применить фильтр", width=20,
                         command=self._refresh)
        bt3_2 = ttk.Button(row3_cf, text="Очистить фильтр", width=20,
                         command=self._clear_filters)

        # Pack row3_cf
        c.pack(in_=row3_cf, side=tk.LEFT)
        bt3_2.pack(side=tk.RIGHT, padx=10, pady=10)
        bt3_1.pack(side=tk.RIGHT, padx=10, pady=10)
        row3_cf.pack(side=tk.TOP, fill=tk.X)

        # Set all filters to default
        self._clear_filters()

        # Text Frame
        preview_cf = ttk.LabelFrame(self, text=' Заявки ', name='preview_cf')

        # column name and width
        #self.headings=('a', 'bb', 'cccc')  # for debug
        self.headings = {'ID': 0, 'InitiatorID':0, '№ заявки': 100,
            'Инициатор': 140, 'Дата создания': 90, 'Дата/время создания': 120,
            'CSP':60, 'МВЗ SAP': 60, 'МВЗ': 150, 'Офис': 100, 'Контрагент': 60,
            'Плановая дата': 90, 'Сумма без НДС': 85, 'Сумма с НДС': 85,
            'Статус': 40, 'Статус заявки': 120, 'Описание': 120,
            'Утверждающий': 120}

        self.table = ttk.Treeview(preview_cf, show='headings',
                                  selectmode=self.selectmode,
                                  style='HeaderStyle.Treeview'
                                  )
        self._init_table(preview_cf)
        self.table.pack(expand=tk.YES, fill=tk.BOTH)
        # allow "select all" operation only for extended selectmode
        if self.selectmode == 'extended':
            self.table.bind('<<select_all>>', self._select_all_rows)

        # Bottom Frame with buttons
        bottom_cf = tk.Frame(self, name='bottom_cf')

        bt1 = ttk.Button(bottom_cf, text="Создать", width=10,
                         command=lambda: controller._show_frame('CreateForm'))
        bt1.pack(side=tk.LEFT, padx=10, pady=10)

        bt2 = ttk.Button(bottom_cf, text="Создать из заявки", width=20,
                         command=self._create_from_current)
        bt2.pack(side=tk.LEFT, padx=10, pady=10)

        if user_info.isSuperUser and user_info.AccessType == 2:
            bt2a = ttk.Button(bottom_cf, text="Выбрать все", width=25,
                             command=self._select_all_rows)
            bt2a.pack(side=tk.LEFT, padx=10, pady=10)
            bt2b = ttk.Button(bottom_cf, text="Утвердить выбранные", width=25,
                             command=self._approve_multiple)
            bt2b.pack(side=tk.LEFT, padx=10, pady=10)

        bt6 = ttk.Button(bottom_cf, text="Выход", width=10,
                         command=controller._quit)
        bt6.pack(side=tk.RIGHT, padx=10, pady=10)

        bt5 = ttk.Button(bottom_cf, text="Подробно", width=10,
                         command=self._show_detail)
        bt5.pack(side=tk.RIGHT, padx=10, pady=10)

        bt4 = ttk.Button(bottom_cf, text="Экспорт в Excel", width=15,
                         command=self._export_to_excel)
        bt4.pack(side=tk.RIGHT, padx=10, pady=10)

        # Pack frames
        bottom_cf.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        preview_cf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

    def  _approve_multiple(self):
        curItems = self.table.selection()
        if not curItems:
            return
        # store paymentID and SumNoTax
        to_approve = {}
        for curRow in curItems:
            request = self.table.item(curRow).get('values')
            # extract all approvable requests for current user
            if request[-1] == self.user_info.ShortUserName:
                to_approve[request[0]] = float(request[11].replace(' ', '')
                                                          .replace(',', '.'))
        if not to_approve:
            return
        appr_sum = '{:,.0f}'.format(sum(to_approve.values())).replace(',', ' ')
        confirmed = messagebox.askyesno(title='Подтвердите действие',
            message='Выбрано заявок: {} на сумму {} грн.\nУтвердить заявки?'
                    .format(len(to_approve), appr_sum)
                                       )
        if not confirmed:
            return
        for paymentID in to_approve.keys():
            self.conn.update_confirmed(self.userID, paymentID, is_approved=True)
        self._refresh()

    def _center_popup_window(self, newlevel, w, h):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        start_x = int((screen_width/2) - (w/2))
        start_y = int((screen_height/2) - (h/2))

        newlevel.geometry('+{}+{}'.format(start_x, start_y))

    def _clear_filters(self):
        self.initiator_box.set('Все')
        self.mvz_box.set('Все')
        self.office_box.set('Все')
        self.plan_date_entry_m.current(datetime.now().month)
        self.year.set(datetime.now().year)
        self.sumtotal_from.set('0,00')
        self.sumtotal_to.set('')
        self.nds.set(-1)
        self.show_for_approve.set(0)

    def _create_from_current(self):
        curRow = self.table.focus()
        if curRow:
            # extract info to be putted in CreateForm
            to_fill = dict(zip(self.table["columns"],
                               self.table.item(curRow).get('values')))
            self.controller._fill_CreateForm(**to_fill)
            self.controller._show_frame('CreateForm')

    def _export_to_excel(self):
        if not self.rows:
            return
        isExported = export_to_excel(self.headings, self.rows)
        if isExported:
            messagebox.showinfo(
                'Экспорт в Excel',
                'Данные экспортированы на рабочий стол'
            )
        else:
            messagebox.showerror(
                'Экспорт в Excel',
                'При экспорте произошла непредвиденная ошибка'
            )


    def _init_table(self, parent):
        if isinstance(self.headings, dict):
            self.table["columns"] = tuple(self.headings.keys())
            self.table["displaycolumns"] = tuple(k for k in self.headings.keys()
                if k not in ('ID', 'НДС', 'Описание', 'Дата/время создания',
                             'МВЗ', 'Статус заявки', 'InitiatorID'))
            for head, width in self.headings.items():
                self.table.heading(head, text=head, anchor=tk.CENTER)
                self.table.column(head, width=width, anchor=tk.CENTER)

        else:
            self.table["columns"] = self.headings
            self.table["displaycolumns"] = self.headings
            for head in self.headings:
                self.table.heading(head, text=head, anchor=tk.CENTER)
                self.table.column(head, width=50*len(head), anchor=tk.CENTER)

        #self._show_rows(rows=((123, 456, 789), ('abc', 'def', 'ghk')))  # for debug

        for tag, bg in zip(('Отм.', 'Утв.', 'Откл.', 'На согл.'),
                           ('lightgray', 'lightgreen', '#f66e6e', '#ffffc8')):
            self.table.tag_configure(tag, background=bg)
        #self.table.tag_configure('oddrow', background='lightgray')

        self.table.bind('<Double-1>', self._show_detail)
        self.table.bind('<Button-1>', self._sort)

        scrolltable = tk.Scrollbar(parent, command=self.table.yview)
        self.table.configure(yscrollcommand=scrolltable.set)
        scrolltable.pack(side=tk.RIGHT, fill=tk.Y)

    def _resize_columns(self):
        for head, width in self.headings.items():
            self.table.column(head, width=width)

    def _row1_pack(self):
        self.initiator_label.pack(side=tk.LEFT)
        self.initiator_box.pack(side=tk.LEFT, padx=5, pady=5)
        self.mvz_label.pack(side=tk.LEFT)
        self.mvz_box.pack(side=tk.LEFT, padx=5, pady=5)
        self.office_box.pack(side=tk.RIGHT, padx=5, pady=5)
        self.office_label.pack(side=tk.RIGHT)

    def _row2_pack(self):
        self.plan_date_label_m.pack(side=tk.LEFT)
        self.plan_date_entry_m.pack(side=tk.LEFT)
        self.plan_date_label_y.pack(side=tk.LEFT)
        self.plan_date_entry_y.pack(side=tk.LEFT, anchor=tk.SW, pady=5)
        self.nds0.pack(side=tk.RIGHT, padx=7)
        self.nds7.pack(side=tk.RIGHT, padx=7)
        self.nds20.pack(side=tk.RIGHT, padx=7)
        self.ndsall.pack(side=tk.RIGHT, padx=7)
        self.nds_label.pack(side=tk.RIGHT, padx=5)
        self.sum_entry_to.pack(side=tk.RIGHT)
        self.sum_label_to.pack(side=tk.RIGHT, padx=2)
        self.sum_entry_from.pack(side=tk.RIGHT)
        self.sum_label_from.pack(side=tk.RIGHT, padx=2)

    def _refresh(self):
        """ Extract information from filters """
        filters = {'initiator': self.initiatorsID[self.initiator_box.current()],
                   'mvz': self.mvzSAP[self.mvz_box.current()],
                   'office': (self.office_box.current() and
                              self.office[self.office_box.current()]),
                   'plan_date_m': self.plan_date_entry_m.current(),
                   'plan_date_y': self.year.get() if self.plan_date_entry_y.get() else 0.,
                   'sumtotal_from': float(self.sumtotal_from.get_float_form()
                                          if self.sum_entry_from.get() else 0),
                   'sumtotal_to': float(self.sumtotal_to.get_float_form()
                                        if self.sum_entry_to.get() else 0),
                   'nds':  self.nds.get(),
                   'just_for_approval': self.show_for_approve.get()
                   }
        self.rows = self.conn.get_paymentslist(self.user_info, **filters)
        self.rows = [tuple(map(lambda val: self._format_float(val)
                               if isinstance(val, Decimal) else val, row))
                     for row in self.rows]
        self._show_rows(self.rows)

    def _select_all_rows(self, event=None):
        all_items = tuple(self.table.get_children())
        self.table.selection_set(all_items)

    def _show_detail(self, event=None):
        """ Show details when double-clicked on row """
        if not event or event.y > 19:
            curRow = self.table.focus()
            if curRow:
                newlevel = tk.Toplevel(self.parent)
                newlevel.transient(self)  # disable minimize/maximize buttons
                newlevel.title('Заявка детально')
                newlevel.iconbitmap('../resources/preview.ico')
                approval = self.table.item(curRow).get('values')[-1]
                # check if current user is approval person
                if self.user_info.ShortUserName == approval and (
                        self.user_info.AccessType == 2
                        or self.user_info.isSuperUser == 1):
                    ApproveConfirmation(newlevel, self, self.conn, self.userID,
                                        self.headings,
                                        self.table.item(curRow).get('values'))
                else:
                    DetailedPreview(newlevel, self, self.conn, self.userID,
                                    self.headings,
                                    self.table.item(curRow).get('values'))
                newlevel.resizable(width=False, height=False)
                self._center_popup_window(newlevel, 500, 400)
                newlevel.focus()
                newlevel.grab_set()
        else:
            # if double click on header - redirect to sorting rows
            self._sort(event)

    def _sort(self, event):
        if self.table.identify_region(event.x, event.y) == 'heading' and self.rows:
            # determine index of displayed column
            disp_col = int(self.table.identify_column(event.x)[1:]) - 1
            # determine index of this column in self.rows
            sort_col = self.table["columns"].index(self.table["displaycolumns"][disp_col])
            self.rows.sort(key=lambda x: x[sort_col],
                           reverse=self.sort_reversed_index == sort_col)
            # store index of last sorted column if sort wasn't reversed
            self.sort_reversed_index = None if self.sort_reversed_index==sort_col else sort_col
            self._show_rows(self.rows)

    def _show_rows(self, rows):
        """ Refresh table with new rows """
        self.table.delete(*self.table.get_children())

        for row in rows:
            # tag = (Status,)
            self.table.insert('', tk.END,
                              values=tuple(row),
                              tags=(row[-4],))


class DetailedPreview(tk.Frame):
    def __init__(self, parent, parentform, conn, userID, head, info):
        super().__init__(parent)
        self.parent = parent
        self.parentform = parentform
        self.conn = conn
        self.approveclass_bool = isinstance(self, ApproveConfirmation)
        self.paymentID, self.initiatorID = info[:2]
        self.userID = userID

        # Top Frame with description and user name
        self.top = tk.Frame(self, name='top_cf', padx=5, pady=5)

        # Create a frame on the canvas to contain the buttons.
        self.table_frame = tk.Frame(self.top)

        # Add info to table_frame
        fonts = (('Calibri', 12, 'bold'), ('Calibri', 12))
        for row in zip(range(len(head)), zip(head, info)):
            if row[1][0] not in ('ID', 'InitiatorID', 'Дата создания',
                                 'Утверждающий', 'Статус'):
                self._newRow(self.table_frame, fonts, *row)

        self.appr_label = tk.Label(self.top, text='Утверждающие',
                                   padx=10, pady=5, font=('Calibri', 12, 'bold'))

        # Top Frame with description and user name
        self.appr_cf = tk.Frame(self, name='appr_cf', padx=5)

        # Add approvals to appr_cf
        fonts = (('Calibri', 12), ('Calibri', 12))
        approvals = self.conn.get_approvals(self.paymentID)
        for rowNumber, row in enumerate(approvals):
            self._newRow(self.appr_cf, fonts, rowNumber+1, row)

        self._add_buttons()
        self._pack_frames()

    def _add_buttons(self):
        # Bottom Frame with buttons
        self.bottom = tk.Frame(self, name='bottom')

        if self.approveclass_bool:
            bt1 = ttk.Button(self.bottom, text="Утвердить", width=10,
                             command=lambda: self._close(True),
                             style='ButtonGreen.TButton')
            bt1.pack(side=tk.LEFT, padx=15, pady=5)

            bt2 = ttk.Button(self.bottom, text="Отклонить", width=10,
                             command=lambda: self._close(False),
                             style='ButtonRed.TButton')
            bt2.pack(side=tk.LEFT, padx=15, pady=5)

        bt4 = ttk.Button(self.bottom, text="Закрыть", width=10,
                         command=self.parent.destroy)
        bt4.pack(side=tk.RIGHT, padx=15, pady=5)

        if self.userID == self.initiatorID:
            bt3 = ttk.Button(self.bottom, text="Отменить", width=10,
                             command=self._discard)
            bt3.pack(side=tk.RIGHT, padx=15, pady=5)

    def _discard(self):
        mboxname = 'Отмена заявки'
        confirmed = messagebox.askyesno(title=mboxname,
                  message='Вы уверены, что хотите отменить заявку?')
        if confirmed:
            self.conn.update_discarded(self.paymentID)
            messagebox.showinfo(mboxname, 'Заявка отменена')
            self.parentform._refresh()
            self.parent.destroy()

    def _newRow(self, frame, fonts, rowNumber, info):
        """ Adds a new line to the table """

        numberOfLines = []       # List to store number of lines needed
        columnWidths = [20, 50]  # Width of the different columns in the table
        stringLength = []        # Lengt of the strings in the info2Add list

        # Find the length of each element in the info2Add list
        for item in info:
            stringLength.append(len(str(item)))
            numberOfLines.append(str(item).count('\n'))

        # Find the number of lines needed for each column
        for index, item in enumerate(stringLength):
            numberOfLines[index] += (ceil(item/columnWidths[index]))

        # Find the maximum number of lines needed
        lineNumber = max(numberOfLines)

        # Define labels (columns) for row
        def form_column(rowNumber, lineNumber, col_num, cell, fonts):
            col = tk.Text(frame, bg='white', padx=3)
            col.insert(1.0, cell)
            col.grid(row=rowNumber, column=col_num+1, sticky='news')
            col.configure(width=columnWidths[col_num], height=lineNumber,
                          font=fonts[col_num], state="disabled")

        for col_num, cell in enumerate(info):
            form_column(rowNumber, lineNumber, col_num, cell, fonts)

    def _pack_frames(self):
        # Pack frames
        self.top.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.bottom.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        self.appr_cf.pack(side=tk.TOP, fill=tk.X)
        self.table_frame.pack()
        self.appr_label.pack(side=tk.LEFT, expand=False)
        self.pack()


class ApproveConfirmation(DetailedPreview):
    def __init__(self, parent, parentform, conn, userID, head, info):
        super().__init__(parent, parentform, conn, userID, head, info)

    def _close(self, is_approved):
        confirmed = messagebox.askyesno(title='Подтвердите действие',
            message='{} заявку?'.format('Утвердить' if is_approved else 'Отклонить'))
        if confirmed:
            self.conn.update_confirmed(self.userID, self.paymentID, is_approved)
            self.parentform._refresh()
            self.parent.destroy()


if __name__ == '__main__':
    from db_connect import DBConnect
    from collections import namedtuple

    UserInfo = namedtuple('UserInfo', ['UserID', 'ShortUserName',
                                       'AccessType', 'isSuperUser'])

    with DBConnect(server='s-kv-center-s59', db='LogisticFinance') as sql:
        try:
            app = PaymentApp(connection=sql,
                             user_info=UserInfo(76, 'TestName', 2, 1),
                             mvz=[('20511RC191', '20511RC191', 'Офис'),
                                  ('40900A2595', '40900A2595', 'Офис')],
                             allowed_initiators=[(None, 'Все'), (1, 2), (3, 4)]
                             )
            app.mainloop()
        except Exception as e:
            print(e)
            raise
    input('Press Enter...')