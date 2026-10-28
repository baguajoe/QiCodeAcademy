// Admin resource definitions: one entry per /api/admin/<key> resource (see API.md).
// Field types: text, email, tel, url, textarea, richtext, select, bool, number, money,
//              date, datetime, image, roles, multi (checkboxes from `options`), program, password, readonly
// `showIf(values)` hides a field unless it applies (e.g. youth-only fields).

export const DIVISIONS = [
  ["youth", "Youth"], ["senior", "Seniors"], ["intergenerational", "Intergenerational"],
];
export const EVENT_DIVISIONS = [...DIVISIONS, ["research", "Research"], ["community", "Community"]];
export const NEIGHBORHOODS = ["Dorchester", "Roxbury", "Mattapan", "Hyde Park", "South End"];
export const STATUS = [["pending", "Pending"], ["confirmed", "Confirmed"], ["waitlist", "Waitlist"], ["cancelled", "Cancelled"]];
export const ROLES = [["coding_mentor", "Coding mentor"], ["wellness_assistant", "Wellness assistant"],
  ["event_help", "Event help"], ["senior_tech_tutor", "Tech tutor for seniors"]];
export const CONTACT_TYPES = [["general", "General"], ["guest_instructor", "Guest instructor"], ["partner", "Partner / sponsor"]];
export const DESIGNATIONS = [["general", "Where needed most"], ["youth", "Youth"], ["senior", "Seniors"], ["research", "Research"]];
export const DONATION_STATUS = [["pending", "Pending"], ["completed", "Completed"], ["failed", "Failed"], ["expired", "Expired"], ["refunded", "Refunded"]];
export const NEWS_CATEGORIES = [["community", "Community"], ["youth", "Youth"], ["seniors", "Seniors"], ["research", "Research"]];
export const TEAM_GROUPS = [["staff", "Staff"], ["board", "Board of Directors"], ["instructor", "Instructor"], ["advisor", "Advisor"]];
export const CURRICULUM_DIVISIONS = [["youth", "Youth"], ["senior", "Seniors"], ["research", "Research"]];
export const CURRICULUM_STATUS = [["available", "Available now"], ["in_development", "In development"]];
// Senior Wellness Day
export const WD_NEIGHBORHOODS = [...NEIGHBORHOODS, "Other"].map((n) => [n, n]);
export const WD_ACTIVITIES = [["tai_chi_baguazhang", "Tai Chi and Baguazhang"], ["chair_yoga_meditation", "Chair yoga and meditation"],
  ["chair_massage", "Chair massage"], ["acupuncture", "Acupuncture"], ["acupressure", "Acupressure"],
  ["strength_balance", "Strength and balance"], ["painting_sewing", "Painting and sewing"], ["wellness_education", "Wellness education"],
  ["marketplace", "Marketplace"], ["food_social", "Food and social time"]];
export const WD_CONTACT = [["email", "Email"], ["phone", "Phone call"], ["text", "Text message"]];
export const WD_FOR = [["myself", "Themselves"], ["someone_else", "A family member or friend"]];
export const WD_TYPES = [["practitioner_massage", "Practitioner (massage)"], ["practitioner_acupuncture", "Practitioner (acupuncture)"],
  ["practitioner_bodywork", "Practitioner (acupressure or other bodywork)"], ["instructor", "Instructor"], ["arts_crafts", "Arts and crafts"],
  ["vendor", "Vendor (sell products)"], ["food_vendor", "Food vendor"], ["resource_table", "Community resource table"],
  ["volunteer", "Volunteer"], ["sponsor", "Sponsor"]];
export const WD_PRACTITIONER_TYPES = ["practitioner_massage", "practitioner_acupuncture", "practitioner_bodywork"];
export const WD_VENDOR_TYPES = ["vendor", "food_vendor"];
export const WD_VENDOR_CATEGORIES = [["crafts", "Crafts"], ["art", "Art"], ["clothing", "Clothing and accessories"], ["jewelry", "Jewelry"],
  ["wellness_products", "Wellness products"], ["food", "Food and drinks"], ["books_media", "Books and media"], ["other", "Other"]];
export const WD_YES_NO = [["yes", "Yes"], ["no", "No"]];
export const WD_STATUS = [["new", "New"], ["contacted", "Contacted"], ["confirmed", "Confirmed"], ["declined", "Declined"]];
export const WD_INSURANCE = [["yes", "Yes"], ["no", "No"], ["not_applicable", "Not applicable"]];
export const WD_COMPENSATION = [["volunteer", "Volunteer"], ["paid", "Paid"], ["open", "Open to discussion"]];
export const WD_SETUP = [["table", "Table"], ["chairs", "Chairs"], ["electricity", "Electricity"], ["tent", "Tent"], ["quiet_space", "Private or quiet space"], ["none", "None"]];
export const WD_AVAILABILITY = [["weekdays", "Weekdays"], ["saturdays", "Saturdays"], ["sundays", "Sundays"]];
export const PARTNER_TYPES = [["community", "Community"], ["sponsor", "Sponsor"], ["research", "Research"]];

const label = (opts) => (v) => (opts.find((o) => o[0] === v) || [v, v])[1];
const yesNo = (v) => (v ? "Yes" : "No");
const dateOnly = (v) => (v ? new Date(v).toLocaleDateString() : "");
const money = (c) => `$${((c || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const labels = (opts) => (list) => (list || []).map(label(opts)).join(", ");
const isYouth = (v) => v.type === "youth";
const isPractitioner = (v) => (v.participation_types || []).some((t) => WD_PRACTITIONER_TYPES.includes(t));
const isVendor = (v) => (v.participation_types || []).some((t) => WD_VENDOR_TYPES.includes(t));
const isSenior = (v) => v.type === "senior";

export const RESOURCES = {
  registrations: {
    label: "Registrations", singular: "registration", group: "People & forms",
    help: "Change a registration's status here. Setting it to Confirmed emails the family or participant automatically.",
    columns: [
      { key: "created_at", label: "Received", format: dateOnly },
      { key: "participant", label: "Participant", get: (r) => `${r.participant_first_name} ${r.participant_last_name}` },
      { key: "program_title", label: "Program" },
      { key: "type", label: "Type", format: label([["youth", "Youth"], ["senior", "Senior"]]) },
      { key: "status", label: "Status", inlineSelect: STATUS },
      { key: "photo_consent", label: "Photo OK?", format: yesNo },
    ],
    filters: [
      { key: "program_id", label: "Program", type: "program" },
      { key: "status", label: "Status", options: STATUS },
      { key: "type", label: "Type", options: [["youth", "Youth"], ["senior", "Senior"]] },
      { key: "photo_consent", label: "Photo consent", options: [["true", "Yes"], ["false", "No"]] },
    ],
    search: "Search names or emails",
    exportCsv: { path: "/admin/registrations/export.csv", filename: "registrations.csv", params: ["program_id", "status"] },
    fields: [
      { key: "program_id", label: "Program", type: "program", required: true },
      { key: "type", label: "Registration type", type: "select", options: [["youth", "Youth (guardian registers)"], ["senior", "Senior"]], required: true },
      { key: "status", label: "Status", type: "select", options: STATUS, hint: "Confirmed sends a confirmation email." },
      { key: "guardian_name", label: "Parent/guardian name", showIf: isYouth, required: true },
      { key: "guardian_email", label: "Parent/guardian email", type: "email", showIf: isYouth, required: true },
      { key: "guardian_phone", label: "Parent/guardian phone", type: "tel", showIf: isYouth, required: true },
      { key: "participant_first_name", label: "Participant first name", required: true },
      { key: "participant_last_name", label: "Participant last name", required: true },
      { key: "grade", label: "Grade", showIf: isYouth, required: true },
      { key: "email", label: "Participant email", type: "email", showIf: isSenior, hint: "Seniors only. Never stored for youth." },
      { key: "phone", label: "Participant phone", type: "tel", showIf: isSenior },
      { key: "emergency_contact_name", label: "Emergency contact name", required: true },
      { key: "emergency_contact_phone", label: "Emergency contact phone", type: "tel", required: true },
      { key: "photo_consent", label: "Photo/video consent given", type: "bool" },
      { key: "guardian_consent", label: "Guardian consent given", type: "bool", showIf: isYouth },
      { key: "comfort_notes", label: "Comfort notes (from participant)", type: "textarea", showIf: isSenior },
      { key: "admin_notes", label: "Staff notes (private)", type: "textarea" },
    ],
  },
  volunteers: {
    label: "Volunteers", singular: "volunteer", group: "People & forms",
    columns: [
      { key: "created_at", label: "Received", format: dateOnly },
      { key: "name", label: "Name" },
      { key: "email", label: "Email" },
      { key: "roles", label: "Roles", format: (r) => (r || []).map(label(ROLES)).join(", ") },
    ],
    search: "Search names or emails",
    exportCsv: { path: "/admin/volunteers/export.csv", filename: "volunteers.csv" },
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "email", label: "Email", type: "email", required: true },
      { key: "phone", label: "Phone", type: "tel" },
      { key: "roles", label: "Roles", type: "roles", required: true },
      { key: "availability", label: "Availability", type: "textarea" },
      { key: "message", label: "Message", type: "textarea" },
    ],
  },
  "contact-messages": {
    label: "Messages", singular: "message", group: "People & forms", autoMarkRead: true,
    help: "Contact form, guest instructor, and partner/sponsor inquiries. Opening a message marks it as read.",
    columns: [
      { key: "is_read", label: "", format: (v) => (v ? "" : "● New"), className: "col-new" },
      { key: "created_at", label: "Received", format: dateOnly },
      { key: "type", label: "Type", format: label(CONTACT_TYPES) },
      { key: "name", label: "From" },
      { key: "subject", label: "Subject" },
    ],
    filters: [
      { key: "type", label: "Type", options: CONTACT_TYPES },
      { key: "is_read", label: "Read?", options: [["false", "Unread"], ["true", "Read"]] },
    ],
    search: "Search name, email, subject",
    fields: [
      { key: "type", label: "Type", type: "select", options: CONTACT_TYPES },
      { key: "name", label: "Name", required: true },
      { key: "email", label: "Email", type: "email", required: true },
      { key: "organization", label: "Organization" },
      { key: "subject", label: "Subject" },
      { key: "message", label: "Message", type: "textarea", required: true },
      { key: "is_read", label: "Mark as read", type: "bool" },
    ],
  },
  "research-inquiries": {
    label: "Research inquiries", singular: "research inquiry", group: "People & forms", autoMarkRead: true,
    columns: [
      { key: "is_read", label: "", format: (v) => (v ? "" : "● New"), className: "col-new" },
      { key: "created_at", label: "Received", format: dateOnly },
      { key: "name", label: "Name" },
      { key: "institution", label: "Institution" },
      { key: "area_of_interest", label: "Interest" },
    ],
    filters: [{ key: "is_read", label: "Read?", options: [["false", "Unread"], ["true", "Read"]] }],
    search: "Search name, institution, email",
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "institution", label: "Institution", required: true },
      { key: "role", label: "Role" },
      { key: "email", label: "Email", type: "email", required: true },
      { key: "area_of_interest", label: "Area of interest" },
      { key: "message", label: "Message", type: "textarea" },
      { key: "is_read", label: "Mark as read", type: "bool" },
    ],
  },
  "research-interest": {
    label: "Research interest list", singular: "sign-up", group: "People & forms",
    help: "People who asked to hear about future research. Joining this list does not enroll anyone in a study.",
    columns: [
      { key: "created_at", label: "Signed up", format: dateOnly },
      { key: "name", label: "Name" },
      { key: "email_or_phone", label: "Email or phone" },
      { key: "neighborhood", label: "Neighborhood" },
    ],
    search: "Search name, contact, neighborhood",
    exportCsv: { path: "/admin/research-interest/export.csv", filename: "research-interest.csv" },
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "email_or_phone", label: "Email or phone", required: true },
      { key: "neighborhood", label: "Neighborhood" },
      { key: "consent_to_contact", label: "Agreed to be contacted", type: "bool", required: true },
    ],
  },
  "wellness-day-interest": {
    label: "Wellness Day interest list", singular: "sign-up", group: "Senior Wellness Day",
    help: "Seniors (or family and friends on their behalf) who want to hear about Senior Wellness Day. We never collect age, health, or medical information.",
    columns: [
      { key: "created_at", label: "Signed up", format: dateOnly },
      { key: "name", label: "Name" },
      { key: "neighborhood", label: "Neighborhood" },
      { key: "activities", label: "Activities", format: labels(WD_ACTIVITIES) },
      { key: "contact_method", label: "Contact by", format: (v) => (v ? label(WD_CONTACT)(v) : "") },
      { key: "wants_to_sell", label: "Senior maker?", format: yesNo },
    ],
    filters: [
      { key: "neighborhood", label: "Neighborhood", options: WD_NEIGHBORHOODS },
      { key: "activity", label: "Activity", options: WD_ACTIVITIES },
      { key: "wants_to_sell", label: "Senior makers", options: [["true", "Senior makers only"], ["false", "Not selling"]] },
    ],
    search: "Search name, email, phone, items",
    exportCsv: { path: "/admin/wellness-day-interest/export.csv", filename: "wellness-day-interest.csv", params: ["neighborhood", "activity", "wants_to_sell"] },
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "email", label: "Email", type: "email", hint: "Email or phone (at least one)." },
      { key: "phone", label: "Phone", type: "tel" },
      { key: "neighborhood", label: "Neighborhood", type: "select", options: WD_NEIGHBORHOODS },
      { key: "activities", label: "Activities of interest", type: "multi", options: WD_ACTIVITIES },
      { key: "contact_method", label: "Preferred contact", type: "select", options: WD_CONTACT },
      { key: "signing_up_for", label: "Signed up for", type: "select", options: WD_FOR },
      { key: "consent_to_contact", label: "Agreed to be contacted about Senior Wellness Day", type: "bool", required: true },
      { key: "wants_to_sell", label: "Senior maker: would like to sell at the Senior Makers Market", type: "bool" },
      { key: "sell_items", label: "What they would sell", showIf: (v) => !!v.wants_to_sell, required: true },
      { key: "needs_table", label: "Needs a table?", type: "select", options: WD_YES_NO, showIf: (v) => !!v.wants_to_sell },
    ],
  },
  "wellness-day-partners": {
    label: "Partners, vendors & volunteers", singular: "submission", group: "Senior Wellness Day",
    help: "Offers to take part in Senior Wellness Day. Nothing here is public. A row appears in \"Who's joining us\" on the website ONLY when its status is Confirmed AND \"Show publicly\" is checked, and then only the organization (or name) and participation type are shown.",
    columns: [
      { key: "created_at", label: "Received", format: dateOnly },
      { key: "display_name", label: "Organization / name" },
      { key: "participation_types", label: "Participating as", format: labels(WD_TYPES) },
      { key: "vendor_category", label: "Vendor category", format: (v) => (v ? label(WD_VENDOR_CATEGORIES)(v) : "") },
      { key: "status", label: "Status", format: label(WD_STATUS) },
      { key: "show_publicly", label: "Public?", format: yesNo },
    ],
    filters: [
      { key: "participation_type", label: "Participating as", options: WD_TYPES },
      { key: "vendor_category", label: "Vendor category", options: WD_VENDOR_CATEGORIES },
      { key: "status", label: "Status", options: WD_STATUS },
      { key: "show_publicly", label: "Public?", options: [["true", "Yes"], ["false", "No"]] },
    ],
    search: "Search name, organization, email, products",
    exportCsv: { path: "/admin/wellness-day-partners/export.csv", filename: "wellness-day-partners.csv", params: ["participation_type", "status", "vendor_category"] },
    fields: [
      { key: "status", label: "Status", type: "select", options: WD_STATUS },
      { key: "show_publicly", label: "Show publicly in \"Who's joining us\" (only when Confirmed)", type: "bool" },
      { key: "admin_notes", label: "Staff notes (private)", type: "textarea" },
      { key: "name", label: "Name", required: true },
      { key: "organization", label: "Organization or business" },
      { key: "email", label: "Email", type: "email", required: true },
      { key: "phone", label: "Phone", type: "tel" },
      { key: "website_or_social", label: "Website or social link" },
      { key: "participation_types", label: "Participating as", type: "multi", options: WD_TYPES, required: true },
      { key: "offer_description", label: "What they would offer", type: "textarea", required: true, hint: "Up to 600 characters." },
      { key: "license_type", label: "License type", showIf: isPractitioner, required: true },
      { key: "license_number", label: "License number", showIf: isPractitioner, required: true,
        hint: "Massage and acupuncture must be provided by Massachusetts-licensed practitioners." },
      { key: "vendor_category", label: "Vendor category", type: "select", options: WD_VENDOR_CATEGORIES, showIf: isVendor },
      { key: "vendor_products", label: "What they sell", showIf: isVendor, required: true },
      { key: "vendor_price_range", label: "Price range", showIf: isVendor },
      { key: "has_insurance", label: "Liability insurance", type: "select", options: WD_INSURANCE },
      { key: "compensation", label: "Volunteer or fee", type: "select", options: WD_COMPENSATION },
      { key: "typical_rate", label: "Typical rate", showIf: (v) => v.compensation === "paid" },
      { key: "setup_needs", label: "Setup needs", type: "multi", options: WD_SETUP },
      { key: "availability", label: "Availability in spring 2027", type: "multi", options: WD_AVAILABILITY },
      { key: "referral_source", label: "How they heard about us" },
      { key: "agrees_not_confirmed", label: "Agreed: submitting doesn't confirm participation", type: "bool" },
      { key: "agrees_respectful", label: "Agreed: treat participants with respect, no high-pressure sales", type: "bool" },
      { key: "agrees_permits", label: "Agreed: responsible for own permits, licenses, and sales tax", type: "bool" },
      { key: "agrees_restricted_products", label: "Agreed: insurance, Medicare plans, and financial products need advance approval", type: "bool" },
      { key: "agrees_no_sales", label: "Agreed (old form): no product sales without approval", type: "bool" },
    ],
  },
  donations: {
    label: "Donations", singular: "donation", group: "People & forms",
    help: "Online donations are recorded automatically by Stripe. Add a row here only for gifts received another way (e.g. by check).",
    columns: [
      { key: "created_at", label: "Date", format: dateOnly },
      { key: "amount_cents", label: "Amount", format: money },
      { key: "recurring", label: "Monthly?", format: yesNo },
      { key: "designation", label: "Designation", format: label(DESIGNATIONS) },
      { key: "donor_name", label: "Donor" },
      { key: "status", label: "Status", format: label(DONATION_STATUS) },
    ],
    filters: [
      { key: "status", label: "Status", options: DONATION_STATUS },
      { key: "designation", label: "Designation", options: DESIGNATIONS },
    ],
    search: "Search donor name or email",
    fields: [
      { key: "amount_cents", label: "Amount ($)", type: "money", required: true },
      { key: "designation", label: "Designation", type: "select", options: DESIGNATIONS },
      { key: "recurring", label: "Monthly gift", type: "bool" },
      { key: "donor_name", label: "Donor name" },
      { key: "donor_email", label: "Donor email", type: "email" },
      { key: "status", label: "Status", type: "select", options: DONATION_STATUS },
      { key: "stripe_session_id", label: "Stripe reference", type: "readonly" },
      { key: "subscription_status", label: "Monthly gift status", type: "readonly" },
    ],
  },
  programs: {
    label: "Programs", singular: "program", group: "Programs & events",
    columns: [
      { key: "title", label: "Title" },
      { key: "division", label: "Division", format: label(DIVISIONS) },
      { key: "neighborhood", label: "Neighborhood" },
      { key: "start_date", label: "Starts" },
      { key: "seats_left", label: "Seats left", format: (v) => (v === null || v === undefined ? "Unlimited" : v) },
      { key: "is_active", label: "Open?", format: yesNo },
    ],
    filters: [{ key: "division", label: "Division", options: DIVISIONS }, { key: "is_active", label: "Open?", options: [["true", "Open"], ["false", "Closed"]] }],
    search: "Search title or location",
    fields: [
      { key: "title", label: "Title", required: true },
      { key: "division", label: "Division", type: "select", options: DIVISIONS, required: true },
      { key: "description", label: "Description", type: "textarea" },
      { key: "age_range", label: "Ages", hint: "e.g. Ages 10–13, or 60+" },
      { key: "schedule", label: "Schedule", hint: "e.g. Saturdays, 10:00 AM – 12:00 PM" },
      { key: "start_date", label: "Start date", type: "date" },
      { key: "end_date", label: "End date", type: "date" },
      { key: "location", label: "Location" },
      { key: "neighborhood", label: "Neighborhood", list: NEIGHBORHOODS },
      { key: "capacity", label: "Capacity (seats)", type: "number", hint: "Leave blank for unlimited. When full, new sign-ups go to the waitlist." },
      { key: "cost", label: "Cost", hint: "e.g. Free, or $20 sliding scale" },
      { key: "image_url", label: "Photo", type: "image", altKey: "image_alt" },
      { key: "is_active", label: "Open for registration", type: "bool" },
      { key: "slug", label: "Web address (slug)", hint: "Optional — created from the title if left blank." },
    ],
  },
  events: {
    label: "Events", singular: "event", group: "Programs & events",
    columns: [
      { key: "start_datetime", label: "Starts", format: (v) => (v ? v.replace("T", " ") : "") },
      { key: "title", label: "Title" },
      { key: "division", label: "Area", format: label(EVENT_DIVISIONS) },
      { key: "neighborhood", label: "Neighborhood" },
      { key: "is_published", label: "Published?", format: yesNo },
    ],
    filters: [{ key: "division", label: "Area", options: EVENT_DIVISIONS }, { key: "is_published", label: "Published?", options: [["true", "Published"], ["false", "Draft"]] }],
    search: "Search title or location",
    fields: [
      { key: "title", label: "Title", required: true },
      { key: "division", label: "Program area", type: "select", options: EVENT_DIVISIONS, required: true },
      { key: "start_datetime", label: "Starts (Boston time)", type: "datetime", required: true },
      { key: "end_datetime", label: "Ends (Boston time)", type: "datetime" },
      { key: "location", label: "Location" },
      { key: "neighborhood", label: "Neighborhood", list: NEIGHBORHOODS },
      { key: "description", label: "Description", type: "textarea" },
      { key: "image_url", label: "Photo", type: "image", altKey: "image_alt" },
      { key: "is_published", label: "Published (visible on the website)", type: "bool" },
      { key: "slug", label: "Web address (slug)", hint: "Optional — created from the title if left blank." },
    ],
  },
  curriculum: {
    label: "Curriculum", singular: "curriculum module", group: "Programs & events",
    help: "Course levels and class descriptions shown on the Youth, Seniors, and Research pages. Empty fields are simply not shown. Describe what happens in class — never promise health outcomes.",
    columns: [
      { key: "sort_order", label: "Order" },
      { key: "title", label: "Title" },
      { key: "division", label: "Division", format: label(CURRICULUM_DIVISIONS) },
      { key: "status", label: "Status", format: label(CURRICULUM_STATUS) },
      { key: "launch_label", label: "Badge" },
      { key: "is_published", label: "Published?", format: yesNo },
    ],
    filters: [
      { key: "division", label: "Division", options: CURRICULUM_DIVISIONS },
      { key: "status", label: "Status", options: CURRICULUM_STATUS },
      { key: "is_published", label: "Published?", options: [["true", "Published"], ["false", "Draft"]] },
    ],
    search: "Search titles",
    fields: [
      { key: "title", label: "Title", required: true, hint: "e.g. Level 1 — Python & Game Development" },
      { key: "division", label: "Division", type: "select", options: CURRICULUM_DIVISIONS, required: true },
      { key: "sort_order", label: "Order on the page", type: "number", hint: "Lower numbers show first." },
      { key: "status", label: "Status", type: "select", options: CURRICULUM_STATUS },
      { key: "launch_label", label: "Badge text", hint: "Short, e.g. \"Launching 2027\". Shown on modules that are in development." },
      { key: "age_range", label: "Ages", hint: "e.g. Ages 14–18" },
      { key: "duration", label: "Length / format", hint: "e.g. 12 weeks · 2 sessions a week · 90 minutes each" },
      { key: "summary", label: "Summary", type: "textarea" },
      { key: "format_notes", label: "Quick facts", type: "lines", hint: "One per line, e.g. Free for families" },
      { key: "learning_goals", label: "What students learn / What we practice", type: "lines", hint: "One item per line." },
      { key: "projects", label: "Weekly projects / Progression", type: "lines", hint: "One per line, in order. For weekly projects use \"Project name — what it teaches\"." },
      { key: "adaptations", label: "Adaptations", type: "textarea", hint: "How the practice is adapted (e.g. for older adults)." },
      { key: "is_published", label: "Published (visible on the website)", type: "bool" },
    ],
  },
  news: {
    label: "News", singular: "news post", group: "Content",
    help: "Posts about our programs must use real photos from our programs — no stock photos.",
    columns: [
      { key: "title", label: "Title" },
      { key: "category", label: "Category", format: label(NEWS_CATEGORIES) },
      { key: "is_published", label: "Published?", format: yesNo },
      { key: "published_at", label: "Date", format: dateOnly },
    ],
    filters: [{ key: "category", label: "Category", options: NEWS_CATEGORIES }, { key: "is_published", label: "Published?", options: [["true", "Published"], ["false", "Draft"]] }],
    search: "Search titles",
    fields: [
      { key: "title", label: "Title", required: true },
      { key: "category", label: "Category", type: "select", options: NEWS_CATEGORIES },
      { key: "cover_image_url", label: "Cover photo", type: "image", altKey: "cover_image_alt" },
      { key: "body", label: "Article", type: "richtext" },
      { key: "is_published", label: "Published (visible on the website)", type: "bool" },
      { key: "slug", label: "Web address (slug)", hint: "Optional — created from the title if left blank." },
    ],
  },
  gallery: {
    label: "Gallery", singular: "photo", group: "Content",
    help: "Only real photos from our programs — never stock photos. Only publish photos where EVERY person pictured (or their parent/guardian) has given photo/video consent.",
    columns: [
      { key: "image_url", label: "Photo", thumb: true },
      { key: "alt_text", label: "Description" },
      { key: "division", label: "Area", format: label(EVENT_DIVISIONS) },
      { key: "consent_confirmed", label: "Consent?", format: yesNo },
      { key: "is_published", label: "Published?", format: yesNo },
    ],
    filters: [{ key: "division", label: "Area", options: EVENT_DIVISIONS }, { key: "is_published", label: "Published?", options: [["true", "Published"], ["false", "Hidden"]] }],
    search: "Search captions",
    fields: [
      { key: "image_url", label: "Photo", type: "image", altKey: "alt_text", required: true },
      { key: "caption", label: "Caption" },
      { key: "division", label: "Program area", type: "select", options: EVENT_DIVISIONS },
      { key: "consent_confirmed", label: "I confirm everyone pictured has given photo/video consent", type: "bool" },
      { key: "is_published", label: "Published (visible on the website)", type: "bool", disabledIf: (v) => !v.consent_confirmed, hint: "Can't be published until consent is confirmed." },
      { key: "sort_order", label: "Sort order", type: "number", hint: "Lower numbers show first." },
    ],
  },
  team: {
    label: "Team", singular: "team member", group: "Content",
    help: "Use real headshots only — never stock photos.",
    columns: [
      { key: "name", label: "Name" },
      { key: "role_title", label: "Role" },
      { key: "group", label: "Group", format: label(TEAM_GROUPS) },
      { key: "sort_order", label: "Order" },
    ],
    filters: [{ key: "group", label: "Group", options: TEAM_GROUPS }],
    search: "Search names",
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "role_title", label: "Role / title" },
      { key: "group", label: "Group", type: "select", options: TEAM_GROUPS },
      { key: "photo_url", label: "Headshot", type: "image", altFromName: true },
      { key: "bio", label: "Bio", type: "textarea", hint: "Separate paragraphs with a blank line." },
      { key: "sort_order", label: "Sort order", type: "number", hint: "Lower numbers show first." },
    ],
  },
  partners: {
    label: "Partners", singular: "partner", group: "Content",
    columns: [{ key: "name", label: "Name" }, { key: "type", label: "Type", format: label(PARTNER_TYPES) }, { key: "sort_order", label: "Order" }],
    filters: [{ key: "type", label: "Type", options: PARTNER_TYPES }],
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "type", label: "Type", type: "select", options: PARTNER_TYPES },
      { key: "website_url", label: "Website", type: "url" },
      { key: "logo_url", label: "Logo", type: "image", altFromName: true },
      { key: "sort_order", label: "Sort order", type: "number" },
    ],
  },
  "impact-stats": {
    label: "Impact stats", singular: "stat", group: "Content",
    help: "Shown on the home page only when at least one stat exists. Use real, verifiable numbers only — never estimates or goals.",
    columns: [{ key: "value", label: "Number" }, { key: "label", label: "Label" }, { key: "sort_order", label: "Order" }],
    fields: [
      { key: "value", label: "Number (as displayed)", required: true, hint: "e.g. 40+" },
      { key: "label", label: "Label", required: true },
      { key: "sort_order", label: "Sort order", type: "number" },
    ],
  },
  "research-references": {
    label: "Research references", singular: "reference", group: "Research",
    help: "Only mark a reference Verified after someone has checked that the source exists, added its link, and confirmed the summary matches it. Unverified references never appear on the website.",
    columns: [{ key: "title", label: "Title" }, { key: "year", label: "Year" }, { key: "url", label: "Link?", format: (v) => (v ? "Yes" : "Missing") }, { key: "is_verified", label: "Verified?", format: yesNo }],
    filters: [{ key: "is_verified", label: "Verified?", options: [["true", "Verified"], ["false", "Not yet"]] }],
    search: "Search title or authors",
    fields: [
      { key: "title", label: "Title", required: true },
      { key: "authors", label: "Authors" },
      { key: "publication", label: "Journal / source", hint: "e.g. BMJ Open, 7(2):e013661" },
      { key: "year", label: "Year", type: "number" },
      { key: "url", label: "Link (DOI or journal page)", type: "url" },
      { key: "summary", label: "Plain-language summary", type: "textarea", hint: "Describe what the study found without overstating it." },
      { key: "is_verified", label: "Verified (show on the Research page)", type: "bool" },
    ],
  },
  users: {
    label: "Admin users", singular: "admin user", group: "Settings",
    columns: [{ key: "email", label: "Email" }, { key: "name", label: "Name" }, { key: "is_active", label: "Active?", format: yesNo }, { key: "last_login_at", label: "Last login", format: dateOnly }],
    fields: [
      { key: "email", label: "Email", type: "email", required: true },
      { key: "name", label: "Name" },
      { key: "is_active", label: "Can log in", type: "bool" },
      { key: "password", label: "New password", type: "password", hint: "At least 10 characters. Leave blank to keep the current password.", requiredOnCreate: true },
    ],
  },
};

export const NAV_GROUPS = ["People & forms", "Senior Wellness Day", "Programs & events", "Content", "Research", "Settings"];

export function newRecordDefaults(key) {
  const defaults = {
    programs: { is_active: true, division: "youth" },
    events: { is_published: false, division: "community" },
    news: { category: "community", is_published: false, body: "" },
    curriculum: { division: "youth", status: "in_development", is_published: false, sort_order: 0 },
    team: { group: "staff", sort_order: 0 },
    partners: { type: "community", sort_order: 0 },
    "impact-stats": { sort_order: 0 },
    gallery: { division: "community", consent_confirmed: false, is_published: false, sort_order: 0 },
    registrations: { type: "youth", status: "pending", photo_consent: false, guardian_consent: false },
    donations: { status: "completed", designation: "general", recurring: false },
    users: { is_active: true },
    "contact-messages": { type: "general" },
    "research-interest": { consent_to_contact: true },
    "wellness-day-interest": { consent_to_contact: true, activities: [], wants_to_sell: false },
    "wellness-day-partners": { status: "new", show_publicly: false, participation_types: [], setup_needs: [], availability: [],
      agrees_not_confirmed: true, agrees_respectful: true, agrees_permits: true, agrees_restricted_products: true },
  };
  return defaults[key] || {};
}
