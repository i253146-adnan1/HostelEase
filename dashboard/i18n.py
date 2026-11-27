"""Presentation-only English/Urdu localization helper for the Warden Dashboard (VS-23).

Stores the UI language preference in the existing server-side Django session
(ADR-003) with zero database schema changes and clean English fallback.
"""

WARDEN_DASHBOARD_LANG_SESSION_KEY = 'warden_dashboard_lang'
SUPPORTED_LANGS = ('en', 'ur')

_WARDEN_STRINGS = {
    'en': {
        'page_title': 'Warden Dashboard — HostelEase',
        'welcome_eyebrow': 'Welcome to HostelEase',
        'welcome_prefix': 'Welcome,',
        'portal_subtitle': 'Warden Portal — Manage hostel operations and student records with ease.',
        'display_picture': 'Display Picture',
        'change_password': 'Change Password',
        'pending_overview': 'Pending Items Overview',
        'total_pending': 'Total Pending:',
        'pending_payment_proofs': 'Pending Payment Proofs',
        'status_pending': 'Status: Pending',
        'review_proofs': 'Review Proofs',
        'open_complaints': 'Open Complaints',
        'status_complaints': 'Status: Submitted / In Progress',
        'manage_complaints': 'Manage Complaints',
        'pending_room_requests': 'Pending Room Requests',
        'review_requests': 'Review Requests',
        'pending_leave_requests': 'Pending Leave Requests',
        'active_leave_requests': 'Active via Leave Requests',
        'leave_module_pending': 'Leave module pending (VS-15)',
        'hostel_info_title': 'Hostel Information',
        'hostel_info_desc': 'Publish announcements, mess menu, and hostel rules.',
        'announcements': 'Announcements',
        'mess_menu': 'Mess Menu',
        'hostel_rules': 'Hostel Rules',
        'students_rooms_title': 'Students & Rooms',
        'students_rooms_desc': 'Manage student accounts, room capacity, and allocations.',
        'student_management': 'Student Management',
        'room_management': 'Room Management',
        'room_swap_requests': 'Room & Swap Requests',
        'finance_ops_title': 'Finance & Operations',
        'finance_ops_desc': 'Review payment proofs, complaints, leave, visitors, and meals.',
        'fees_payments': 'Fees & Payments',
        'complaints': 'Complaints',
        'leave_requests': 'Leave Requests',
        'visitor_log': 'Visitor Log',
        'meal_optouts': 'Meal Opt-Outs',
        'feedback_summary': 'Feedback Summary',
        # Navigation (used on Warden Dashboard when Urdu is active)
        'nav_overview': 'Overview',
        'nav_dashboard': 'Dashboard',
        'nav_residents_rooms': 'Residents & Rooms',
        'nav_students': 'Students',
        'nav_rooms': 'Rooms',
        'nav_room_requests': 'Room Requests',
        'nav_finance': 'Finance',
        'nav_fee_ledger': 'Fee Ledger',
        'nav_pending_proofs': 'Pending Proofs',
        'nav_operations': 'Operations',
        'nav_feedback': 'Feedback',
        'nav_hostel_info': 'Hostel Info',
        'nav_rules': 'Rules',
        'nav_logout': 'Logout',
    },
    'ur': {
        'page_title': 'وارڈن ڈیش بورڈ — ہاسٹل ایز',
        'welcome_eyebrow': 'ہاسٹل ایز میں خوش آمدید',
        'welcome_prefix': 'خوش آمدید،',
        'portal_subtitle': 'وارڈن پورٹل — ہاسٹل کے کام اور طلبہ کا ریکارڈ آسانی سے سنبھالیں۔',
        'display_picture': 'پروفائل تصویر',
        'change_password': 'پاس ورڈ بدلیں',
        'pending_overview': 'باقی کاموں کی تفصیل',
        'total_pending': 'کل باقی:',
        'pending_payment_proofs': 'فیس کی باقی رسیدیں',
        'status_pending': 'حالت: باقی',
        'review_proofs': 'رسیدیں چیک کریں',
        'open_complaints': 'باقی شکایات',
        'status_complaints': 'حالت: نئی / جاری',
        'manage_complaints': 'شکایات دیکھیں',
        'pending_room_requests': 'کمرے کی باقی درخواستیں',
        'review_requests': 'درخواستیں دیکھیں',
        'pending_leave_requests': 'چھٹی کی باقی درخواستیں',
        'active_leave_requests': 'چھٹی کی درخواستیں دیکھیں',
        'leave_module_pending': 'چھٹی کا سیکشن ابھی باقی ہے (VS-15)',
        'hostel_info_title': 'ہاسٹل کی معلومات',
        'hostel_info_desc': 'اعلانات، کھانے کا مینو اور ہاسٹل کے اصول لگائیں۔',
        'announcements': 'اعلانات',
        'mess_menu': 'کھانے کا مینو',
        'hostel_rules': 'ہاسٹل کے اصول',
        'students_rooms_title': 'طلبہ اور کمرے',
        'students_rooms_desc': 'طلبہ کے اکاؤنٹس، کمروں کی جگہ اور کمرے دینے کا کام سنبھالیں۔',
        'student_management': 'طلبہ کا ریکارڈ',
        'room_management': 'کمروں کی تفصیل',
        'room_swap_requests': 'کمرے اور تبدیلی کی درخواستیں',
        'finance_ops_title': 'فیس اور دیگر کام',
        'finance_ops_desc': 'فیس رسیدیں، شکایات، چھٹی، مہمان اور کھانے کی تفصیل دیکھیں۔',
        'fees_payments': 'فیس اور ادائیگیاں',
        'complaints': 'شکایات',
        'leave_requests': 'چھٹی کی درخواستیں',
        'visitor_log': 'مہمانوں کا ریکارڈ',
        'meal_optouts': 'کھانے کی چھٹی',
        'feedback_summary': 'طلبہ کی رائے',
        # Navigation
        'nav_overview': 'خلاصہ',
        'nav_dashboard': 'ڈیش بورڈ',
        'nav_residents_rooms': 'طلبہ اور کمرے',
        'nav_students': 'طلبہ',
        'nav_rooms': 'کمرے',
        'nav_room_requests': 'کمرے کی درخواستیں',
        'nav_finance': 'فیس اور پیسے',
        'nav_fee_ledger': 'فیس کھاتہ',
        'nav_pending_proofs': 'باقی رسیدیں',
        'nav_operations': 'روزمرہ کام',
        'nav_feedback': 'رائے',
        'nav_hostel_info': 'ہاسٹل معلومات',
        'nav_rules': 'اصول',
        'nav_logout': 'لاگ آؤٹ',
    },
}


def get_warden_dashboard_lang(request):
    """Return the normalized Warden Dashboard UI language ('en' or 'ur')."""
    lang = request.session.get(WARDEN_DASHBOARD_LANG_SESSION_KEY, 'en')
    return lang if lang in SUPPORTED_LANGS else 'en'


def set_warden_dashboard_lang(request, lang):
    """Persist a validated Warden Dashboard UI language in the session."""
    normalized = lang if lang in SUPPORTED_LANGS else 'en'
    request.session[WARDEN_DASHBOARD_LANG_SESSION_KEY] = normalized
    return normalized


def get_warden_dashboard_i18n(request):
    """Build presentation context for Warden Dashboard English/Urdu rendering."""
    lang = get_warden_dashboard_lang(request)
    is_urdu = lang == 'ur'
    return {
        'lang': lang,
        'is_urdu': is_urdu,
        'dir': 'rtl' if is_urdu else 'ltr',
        't': _WARDEN_STRINGS[lang],
    }
