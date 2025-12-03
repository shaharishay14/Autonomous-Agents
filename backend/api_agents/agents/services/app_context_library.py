"""
Application Context Library
---------------------------
Provides expert-level guidance for each integrated application.
Each function returns concise, actionable context about how to use that app effectively.

Design Principles:
- Token-efficient (150-300 tokens per app)
- Action-oriented (what to DO, not just what the app is)
- Covers common workflows and pitfalls
- Includes dependency chains (e.g., Download before Attach)
"""

import datetime
from typing import Dict, Callable


def get_gmail_context() -> str:
    """Gmail - Email management"""
    return """
📧 **GMAIL GUIDANCE**
• **Sending Emails**: Use GMAIL_SEND_EMAIL for text emails. For attachments, use GMAIL_SEND_EMAIL_WITH_ATTACHMENT.
• **Attachments from Drive**: FIRST download the file using GOOGLEDRIVE_DOWNLOAD_FILE, THEN attach to email.
• **Searching**: Use GMAIL_SEARCH_EMAILS with queries like "from:user@example.com" or "subject:report".
• **Threading**: Emails automatically thread by subject. Use "Re:" prefix to continue threads.
• **Verification**: After sending, assume success unless you get an error. Don't retry without confirmation.
• **Common Pattern**: User says "email this file" → Search Drive → Download → Send with attachment.
"""


def get_googledrive_context() -> str:
    """Google Drive - File storage and management"""
    return """
📁 **GOOGLE DRIVE GUIDANCE**
• **Finding Files**: Use GOOGLEDRIVE_FIND_FILE with name/keyword search first.
• **Downloading**: Always download files with GOOGLEDRIVE_DOWNLOAD_FILE before attaching or reading content.
• **Uploading**: Use GOOGLEDRIVE_UPLOAD_FILE. Check for existing files first to avoid duplicates.
• **Sharing**: After upload, use GOOGLEDRIVE_GET_FILE_LINK to get shareable URL if needed.
• **Common Workflow**: Find → Download → Use (attach/send/analyze).
• **Links vs Files**: If user shares a Drive link, extract file ID and download the actual file.
"""


def get_googlecalendar_context() -> str:
    """Google Calendar - Event and meeting management"""
    return """
📅 **GOOGLE CALENDAR GUIDANCE**
• **CRITICAL - Avoid Duplicates**: ALWAYS search with GOOGLECALENDAR_FIND_EVENT before creating events.
• **Creating Events**: Use GOOGLECALENDAR_CREATE_EVENT with title, start_time, end_time, timezone.
• **Time Format**: Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS). Default to user's timezone.
• **Searching**: Search by date range, title keywords, or attendee email.
• **Today's Date**: Current date is {current_date}. Use this when user says "today" or "tomorrow".
• **Verification**: After creating, search to confirm the event exists before confirming to user.
• **Meeting Passwords**: Calendar events don't have passwords. If user asks, clarify they need Zoom/Meet link.
""".format(current_date=datetime.datetime.now().strftime("%Y-%m-%d"))


def get_slack_context() -> str:
    """Slack - Team messaging"""
    return """
💬 **SLACK GUIDANCE**
• **Sending Messages**: Use SLACK_SEND_MESSAGE with channel ID or name.
• **Channels vs DMs**: Channels start with #. DMs need user ID (use SLACK_FIND_USER first).
• **Finding Channels**: Use SLACK_LIST_CHANNELS to get channel IDs.
• **File Sharing**: Use SLACK_UPLOAD_FILE. Download from Drive first if needed.
• **Formatting**: Slack uses markdown. Use *bold*, _italic_, `code`, ```code block```.
• **Mentions**: Use <@USER_ID> to mention users, <#CHANNEL_ID> for channels.
"""


def get_twitter_context() -> str:
    """Twitter/X - Social media posting"""
    return """
🐦 **TWITTER GUIDANCE**
• **Authentication**: You are already logged in as the user. Never ask for credentials.
• **Posting**: Use TWITTER_CREATE_TWEET. Character limit is 280 characters.
• **Media**: For images/videos, use TWITTER_UPLOAD_MEDIA first, then attach media_id to tweet.
• **Threads**: Post multiple tweets sequentially, using previous tweet ID as reply_to.
• **Verification**: After posting, assume success unless error. Do NOT retry without confirmation.
• **Best Practice**: Keep tweets concise, engaging, and under 280 chars.
"""


def get_instagram_context() -> str:
    """Instagram - Photo and video sharing"""
    return """
📸 **INSTAGRAM GUIDANCE**
• **Authentication**: You are already authenticated. NEVER ask for user's Instagram handle.
• **Posting**: Use INSTAGRAM_CREATE_POST with image URL or file path.
• **Media Requirements**: Images must be JPG/PNG. Videos must be MP4. Max 10 photos per post.
• **Captions**: Up to 2,200 characters. Use hashtags and @mentions naturally.
• **Stories**: Use INSTAGRAM_CREATE_STORY for 24-hour content.
• **Verification**: After posting, assume success unless error returned.
"""


def get_linkedin_context() -> str:
    """LinkedIn - Professional networking"""
    return """
💼 **LINKEDIN GUIDANCE**
• **Authentication**: Already connected as the user. No need to ask for credentials.
• **Posting**: Use LINKEDIN_CREATE_POST for text, images, or articles.
• **Professional Tone**: Maintain professional language. Use industry-relevant hashtags.
• **Media**: Upload images/documents with LINKEDIN_UPLOAD_MEDIA first, then attach.
• **Visibility**: Posts are public by default unless specified otherwise.
• **Best Practice**: Focus on professional insights, achievements, and industry news.
"""


def get_github_context() -> str:
    """GitHub - Code repository management"""
    return """
💻 **GITHUB GUIDANCE**
• **Repository Format**: Use "owner/repo" format (e.g., "facebook/react").
• **Issues**: Create with GITHUB_CREATE_ISSUE. Include title, body, and labels.
• **Pull Requests**: Use GITHUB_CREATE_PR with base and head branches.
• **File Operations**: Use GITHUB_GET_FILE to read, GITHUB_CREATE_OR_UPDATE_FILE to write.
• **Searching**: Use GITHUB_SEARCH_REPOS or GITHUB_SEARCH_CODE for finding repositories/code.
• **Authentication**: You have full access to user's repositories (public and private).
"""


def get_notion_context() -> str:
    """Notion - Note-taking and knowledge management"""
    return """
📝 **NOTION GUIDANCE**
• **Pages**: Create with NOTION_CREATE_PAGE. Pages need a parent (database or page ID).
• **Databases**: Query with NOTION_QUERY_DATABASE. Filter and sort results.
• **Content**: Use Notion's block structure. Common blocks: paragraph, heading, list, code.
• **Finding Content**: Use NOTION_SEARCH to find pages/databases by title.
• **Updating**: Use NOTION_UPDATE_PAGE to modify existing pages.
• **Structure**: Notion is hierarchical - pages can contain pages (like folders).
"""


def get_asana_context() -> str:
    """Asana - Project and task management"""
    return """
✅ **ASANA GUIDANCE**
• **Tasks**: Create with ASANA_CREATE_TASK. Requires project ID or workspace ID.
• **Projects**: List with ASANA_GET_MULTIPLE_PROJECTS, create with ASANA_CREATE_A_PROJECT.
• **Assignments**: Assign tasks with assignee user ID (use ASANA_GET_MULTIPLE_USERS to find).
• **Due Dates**: Use ISO 8601 format (YYYY-MM-DD) for due dates.
• **Subtasks**: Create with ASANA_CREATE_SUBTASK under parent task.
• **Status**: Update with ASANA_UPDATE_A_TASK to mark complete or change status.
"""


def get_trello_context() -> str:
    """Trello - Board-based project management"""
    return """
📋 **TRELLO GUIDANCE**
• **Boards → Lists → Cards**: Trello hierarchy. Cards are tasks, Lists are columns, Boards are projects.
• **Creating Cards**: Use TRELLO_CREATE_CARD. Needs list ID (get from TRELLO_GET_LISTS_ON_BOARD).
• **Moving Cards**: Use TRELLO_UPDATE_CARD to change list or position.
• **Attachments**: Add files with TRELLO_ADD_ATTACHMENT_TO_CARD.
• **Checklists**: Create with TRELLO_ADD_CHECKLIST_TO_CARD for sub-tasks.
• **Finding Boards**: Use TRELLO_GET_BOARDS to list all user boards.
"""


def get_zoom_context() -> str:
    """Zoom - Video conferencing"""
    return """
🎥 **ZOOM GUIDANCE**
• **Creating Meetings**: Use ZOOM_CREATE_MEETING with topic, start_time, duration.
• **Meeting Types**: Instant (type=1), Scheduled (type=2), Recurring (type=8).
• **Settings**: Include waiting_room, password, join_before_host as needed.
• **Time Format**: Use ISO 8601 (YYYY-MM-DDTHH:MM:SS) for start times.
• **Response**: Returns join_url (for participants) and start_url (for host).
• **Calendar Integration**: After creating, can add join_url to calendar event description.
"""


def get_shopify_context() -> str:
    """Shopify - E-commerce management"""
    return """
🛒 **SHOPIFY GUIDANCE**
• **Products**: Create/update with SHOPIFY_CREATE_PRODUCT, get with SHOPIFY_GET_PRODUCT.
• **Orders**: List with SHOPIFY_GET_ORDERS, update fulfillment status.
• **Inventory**: Track with SHOPIFY_UPDATE_INVENTORY_LEVEL.
• **Customers**: Manage with SHOPIFY_CREATE_CUSTOMER, SHOPIFY_GET_CUSTOMERS.
• **Required Fields**: Products need title, price, and inventory_quantity minimum.
• **Images**: Add product images with URLs using SHOPIFY_ADD_PRODUCT_IMAGE.
"""


def get_stripe_context() -> str:
    """Stripe - Payment processing"""
    return """
💳 **STRIPE GUIDANCE**
• **Payments**: Create with STRIPE_CREATE_PAYMENT_INTENT. Amount in smallest currency unit (cents).
• **Customers**: Create with STRIPE_CREATE_CUSTOMER before charging.
• **Invoices**: Generate with STRIPE_CREATE_INVOICE for recurring billing.
• **Refunds**: Process with STRIPE_CREATE_REFUND using payment_intent ID.
• **Testing**: Stripe has test/live modes. Confirm which mode before operations.
• **Currency**: Always specify currency (e.g., "usd"). Amount is in cents (e.g., 1000 = $10.00).
"""


def get_airtable_context() -> str:
    """Airtable - Database and spreadsheet hybrid"""
    return """
🗄️ **AIRTABLE GUIDANCE**
• **Structure**: Bases → Tables → Records. Similar to Database → Table → Row.
• **Creating Records**: Use AIRTABLE_CREATE_RECORD with base ID, table name, and fields dict.
• **Querying**: Use AIRTABLE_LIST_RECORDS with filters (e.g., "{Status}='Active'").
• **Field Types**: Text, Number, Checkbox, Date, Attachment, Link to another record.
• **Batch Operations**: Use AIRTABLE_CREATE_MULTIPLE_RECORDS for efficiency.
• **Finding Bases**: Use AIRTABLE_LIST_BASES to get available bases and their IDs.
"""


def get_reddit_context() -> str:
    """Reddit - Community discussion platform"""
    return """
🔴 **REDDIT GUIDANCE**
• **Authentication**: Already logged in as user. Never ask for credentials.
• **Posting**: Use REDDIT_SUBMIT_POST with subreddit name (without r/ prefix).
• **Post Types**: text, link, or image. Text posts need title + body, links need title + url.
• **Commenting**: Use REDDIT_SUBMIT_COMMENT with post ID.
• **Subreddit Rules**: Be aware posts may be removed if they violate subreddit rules.
• **Verification**: Check post status after submission. May be filtered by automoderator.
"""


def get_whatsapp_context() -> str:
    """WhatsApp - Messaging platform"""
    return """
💬 **WHATSAPP GUIDANCE**
• **Business API**: This uses WhatsApp Business API, not personal WhatsApp.
• **Sending Messages**: Use WHATSAPP_SEND_MESSAGE with phone number (include country code).
• **Phone Format**: Use E.164 format: +1234567890 (plus sign + country code + number).
• **Templates**: Some messages require pre-approved templates for initial contact.
• **Media**: Send images/files with WHATSAPP_SEND_MEDIA.
• **24-Hour Window**: Can freely message within 24 hours of user's last message.
"""


def get_googledocs_context() -> str:
    """Google Docs - Document creation and editing"""
    return """
📄 **GOOGLE DOCS GUIDANCE**
• **Creating Docs**: Use GOOGLEDOCS_CREATE_DOCUMENT with title.
• **Reading Content**: Use GOOGLEDOCS_GET_DOCUMENT to fetch full content.
• **Editing**: Use GOOGLEDOCS_UPDATE_DOCUMENT with batch update requests.
• **Formatting**: Supports bold, italic, headings, lists, tables.
• **Sharing**: After creating, use Drive sharing tools to make accessible.
• **Collaboration**: Multiple users can edit simultaneously - check for conflicts.
"""


def get_googlesheets_context() -> str:
    """Google Sheets - Spreadsheet management"""
    return """
📊 **GOOGLE SHEETS GUIDANCE**
• **Creating Sheets**: Use GOOGLESHEETS_CREATE_SPREADSHEET with title and sheet names.
• **Reading Data**: Use GOOGLESHEETS_GET_VALUES with range (e.g., "Sheet1!A1:D10").
• **Writing Data**: Use GOOGLESHEETS_UPDATE_VALUES with range and 2D array of values.
• **Formulas**: Can write formulas like "=SUM(A1:A10)" in cells.
• **Batch Operations**: Use GOOGLESHEETS_BATCH_UPDATE for multiple changes at once.
• **Range Format**: Use A1 notation (e.g., "Sheet1!A1:B5" or "Sheet1!A:A" for entire column).
"""


def get_clickup_context() -> str:
    """ClickUp - Project management"""
    return """
📌 **CLICKUP GUIDANCE**
• **Hierarchy**: Workspace → Space → Folder → List → Task.
• **Creating Tasks**: Use CLICKUP_CREATE_A_TASK with list ID, name, and optional details.
• **Finding Lists**: Use CLICKUP_GET_LISTS to find list IDs in spaces.
• **Due Dates**: Unix timestamp in milliseconds (use current time * 1000).
• **Assignees**: Add user IDs with CLICKUP_ADD_TASK_ASSIGNEE.
• **Statuses**: Use CLICKUP_UPDATE_TASK_STATUS to move through workflow.
"""


def get_dropbox_context() -> str:
    """Dropbox - File storage and sharing"""
    return """
📦 **DROPBOX GUIDANCE**
• **Paths**: All paths start with "/" (e.g., "/Documents/file.pdf").
• **Uploading**: Use DROPBOX_UPLOAD_FILE with path and file content.
• **Downloading**: Use DROPBOX_DOWNLOAD_FILE to get file content.
• **Sharing**: Use DROPBOX_CREATE_SHARED_LINK to generate shareable URLs.
• **Search**: Use DROPBOX_SEARCH for finding files by name/content.
• **Folders**: Create with DROPBOX_CREATE_FOLDER. Nested paths are automatically created.
"""


def get_monday_context() -> str:
    """Monday.com - Work management"""
    return """
📋 **MONDAY.COM GUIDANCE**
• **Structure**: Boards → Groups → Items → Columns.
• **Creating Items**: Use MONDAY_CREATE_ITEM with board ID, group ID, and item name.
• **Column Values**: Update with MONDAY_UPDATE_ITEM_COLUMN_VALUES (JSON format).
• **Querying**: Use MONDAY_EXECUTE_QUERY with GraphQL syntax.
• **Board IDs**: Get with MONDAY_GET_BOARDS or ask user for specific board.
• **Status Columns**: Use label text (e.g., "Done", "In Progress") not IDs.
"""


def get_linear_context() -> str:
    """Linear - Issue tracking"""
    return """
🎯 **LINEAR GUIDANCE**
• **Creating Issues**: Use LINEAR_CREATE_ISSUE with team ID, title, description.
• **Teams**: Get team IDs with LINEAR_GET_TEAMS.
• **Status**: Issues have states (Backlog, Todo, In Progress, Done, Canceled).
• **Priority**: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low.
• **Assignees**: Assign with user ID (get from LINEAR_GET_USERS).
• **Projects**: Group related issues with LINEAR_CREATE_PROJECT.
"""


def get_figma_context() -> str:
    """Figma - Design and prototyping"""
    return """
🎨 **FIGMA GUIDANCE**
• **Files**: Design files have unique file keys (from URL).
• **Reading**: Use FIGMA_GET_FILE to fetch design data and structure.
• **Comments**: Add with FIGMA_POST_COMMENT on specific nodes.
• **Exporting**: Use FIGMA_GET_IMAGE to export designs as PNG/JPG/SVG.
• **Teams**: List projects with FIGMA_GET_TEAM_PROJECTS.
• **Collaboration**: Figma is real-time - changes sync automatically.
"""


def get_canva_context() -> str:
    """Canva - Graphic design"""
    return """
🎨 **CANVA GUIDANCE**
• **Creating Designs**: Use CANVA_CREATE_CANVA_DESIGN with template or blank.
• **Templates**: Browse with CANVA_ACCESS_USER_SPECIFIC_BRAND_TEMPLATES_LIST.
• **Exporting**: Use CANVA_CREATE_CANVA_DESIGN_EXPORT_JOB for PNG/JPG/PDF.
• **Brand Assets**: Upload with CANVA_CREATE_ASSET_UPLOAD_JOB.
• **Folders**: Organize with CANVA_CREATE_USER_OR_SUB_FOLDER.
• **Editing**: Canva designs are edited in web UI - API is for automation.
"""


def get_todoist_context() -> str:
    """Todoist - Task management"""
    return """
✅ **TODOIST GUIDANCE**
• **Creating Tasks**: Use TODOIST_CREATE_TASK with content (task name) required.
• **Due Dates**: Use natural language ("today", "tomorrow", "next Monday") or ISO format.
• **Projects**: Group tasks with TODOIST_CREATE_PROJECT first, then add tasks to it.
• **Priority**: 1=Normal, 2=Medium, 3=High, 4=Urgent.
• **Labels**: Add with TODOIST_ADD_LABEL_TO_TASK for categorization.
• **Completing**: Use TODOIST_COMPLETE_TASK - don't delete unless user explicitly asks.
"""


def get_outlook_context() -> str:
    """Outlook - Email and calendar (Microsoft)"""
    return """
📧 **OUTLOOK GUIDANCE**
• **Email**: Use OUTLOOK_SEND_EMAIL similar to Gmail. Supports HTML content.
• **Attachments**: Use OUTLOOK_SEND_EMAIL_WITH_ATTACHMENT for files.
• **Calendar**: Use OUTLOOK_CREATE_EVENT for meetings. Supports recurrence.
• **Folders**: Organize emails with OUTLOOK_MOVE_MESSAGE to folders.
• **Search**: Use OUTLOOK_SEARCH_MESSAGES with keyword queries.
• **Time Format**: Use ISO 8601 (YYYY-MM-DDTHH:MM:SS) with timezone.
"""


def get_facebook_context() -> str:
    """Facebook - Social networking"""
    return """
📘 **FACEBOOK GUIDANCE**
• **Authentication**: Already authenticated. Never ask for credentials.
• **Posting**: Use FACEBOOK_CREATE_POST with message text.
• **Media**: Upload photos/videos with FACEBOOK_UPLOAD_PHOTO or FACEBOOK_UPLOAD_VIDEO first.
• **Pages vs Profile**: Specify page_id if posting to a page, not personal profile.
• **Privacy**: Default is friends-only unless specified otherwise.
• **Best Practice**: Keep posts engaging and under 250 characters for best reach.
"""


def get_googlemeet_context() -> str:
    """Google Meet - Video conferencing"""
    return """
🎥 **GOOGLE MEET GUIDANCE**
• **Creating Meetings**: Use GOOGLEMEET_CREATE_MEETING to generate meeting URL.
• **Calendar Integration**: Meetings are automatically added to Calendar when created via event.
• **Instant vs Scheduled**: Create instant meeting or attach to calendar event.
• **Meeting Codes**: Each meeting has a unique code (e.g., "abc-defg-hij").
• **Settings**: Control lobby, recording, and participant permissions.
• **Access**: Meeting URLs can be shared directly with participants.
"""


def get_googleslides_context() -> str:
    """Google Slides - Presentation software"""
    return """
📽️ **GOOGLE SLIDES GUIDANCE**
• **Creating**: Use GOOGLESLIDES_CREATE_PRESENTATION with title.
• **Slides**: Add with GOOGLESLIDES_CREATE_SLIDE. Each slide has unique ID.
• **Content**: Add text, images, shapes with batch update requests.
• **Templates**: Can apply predefined layouts and master slides.
• **Reading**: Use GOOGLESLIDES_GET_PRESENTATION to fetch all content.
• **Sharing**: Use Drive sharing after creation for collaboration.
"""


# === CONTEXT REGISTRY ===
# Maps app names (from composio_config.py) to their context functions

CONTEXT_REGISTRY: Dict[str, Callable[[], str]] = {
    "GMAIL": get_gmail_context,
    "GOOGLEDRIVE": get_googledrive_context,
    "GOOGLECALENDAR": get_googlecalendar_context,
    "SLACK": get_slack_context,
    "TWITTER": get_twitter_context,
    "INSTAGRAM": get_instagram_context,
    "LINKEDIN": get_linkedin_context,
    "GITHUB": get_github_context,
    "NOTION": get_notion_context,
    "ASANA": get_asana_context,
    "ZOOM": get_zoom_context,
    "SHOPIFY": get_shopify_context,
    "STRIPE": get_stripe_context,
    "AIRTABLE": get_airtable_context,
    "REDDIT": get_reddit_context,
    "WHATSAPP": get_whatsapp_context,
    "GOOGLEDOCS": get_googledocs_context,
    "GOOGLESHEETS": get_googlesheets_context,
    "CLICKUP": get_clickup_context,
    "DROPBOX": get_dropbox_context,
    "MONDAY": get_monday_context,
    "LINEAR": get_linear_context,
    "FIGMA": get_figma_context,
    "CANVA": get_canva_context,
    "TODOIST": get_todoist_context,
    "OUTLOOK": get_outlook_context,
    "FACEBOOK": get_facebook_context,
    "GOOGLEMEET": get_googlemeet_context,
    "GOOGLESLIDES": get_googleslides_context,
}


def get_app_context(app_name: str) -> str:
    """
    Get expert context for a specific app.

    Args:
        app_name: Application name (e.g., "GMAIL", "SLACK")

    Returns:
        Context string with guidance for that app, or empty string if not found
    """
    context_func = CONTEXT_REGISTRY.get(app_name.upper())
    if context_func:
        try:
            return context_func()
        except Exception as e:
            print(f"⚠️  Error getting context for {app_name}: {e}")
            return ""
    return ""


def get_contexts_for_connected_apps(connected_apps: list) -> str:
    """
    Get combined context for all connected apps.

    Args:
        connected_apps: List of app names (e.g., ["GMAIL", "SLACK", "GOOGLEDRIVE"])

    Returns:
        Combined context string with guidance for all connected apps
    """
    if not connected_apps:
        return ""

    contexts = []
    contexts.append("\n" + "="*80)
    contexts.append("📚 APPLICATION-SPECIFIC GUIDANCE")
    contexts.append("="*80)
    contexts.append("Below is expert guidance for each connected application.\n")

    for app in connected_apps:
        context = get_app_context(app)
        if context:
            contexts.append(context)

    contexts.append("="*80 + "\n")

    return "\n".join(contexts)
