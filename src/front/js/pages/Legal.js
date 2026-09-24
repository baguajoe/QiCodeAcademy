// Privacy Policy and Terms of Use — PLACEHOLDER DRAFTS. Have a qualified
// reviewer (ideally an attorney) replace/approve this text before launch.
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";
import { useStore } from "../store/appContext";

function DraftBanner() {
  const { t } = useTranslation();
  return <p className="alert alert-warning" role="note"><strong>{t("legal.draft")}</strong></p>;
}

function ContactLine() {
  const { actions } = useStore();
  const email = actions.setting("org_contact_email");
  return email ? <>by email at <a href={`mailto:${email}`}>{email}</a> or </> : null;
}

export function Privacy() {
  const { t } = useTranslation();
  useSeo({ title: t("legal.privacyTitle"), noindex: true });
  return (
    <section className="section">
      <div className="container prose">
        <DraftBanner />
        <h1>{t("legal.privacyTitle")}</h1>
        <p><em>Last updated: [DATE — fill in at launch]</em></p>
        <p>Qi Code Academy, Inc. ("Qi Code Academy," "we") respects your privacy. This policy explains what information we collect through this website and how we use it.</p>
        <h2>Information we collect</h2>
        <ul>
          <li><strong>Program registrations:</strong> For youth programs, we collect the parent or guardian's name, email, and phone; the student's first and last name and grade; an emergency contact; and photo/video and guardian consent choices. <strong>We do not collect a youth participant's own email address or phone number.</strong> For senior programs, we collect the participant's name, email and/or phone, an emergency contact, photo/video consent, and any optional comfort notes they choose to share.</li>
          <li><strong>Volunteer, contact, and partnership forms:</strong> the name, contact details, and message you provide.</li>
          <li><strong>Research interest list:</strong> your name, an email or phone number, and (optionally) your neighborhood. We do not collect health or medical information through this website. Joining this list does not enroll you in any study.</li>
          <li><strong>Donations:</strong> payments are processed by Stripe. We receive your name, email, gift amount, and designation, but not your full card number.</li>
          <li><strong>Site preferences:</strong> your text-size, contrast, and language choices are saved in your own browser.</li>
        </ul>
        <h2>How we use information</h2>
        <p>We use this information to run our programs, respond to you, send confirmations and receipts, keep participants safe, and share updates you have asked for. We do not sell personal information.</p>
        <h2>Service providers</h2>
        <p>We use trusted providers to operate this site, such as web hosting, email delivery, image storage, and Stripe for payments. They may process information only on our behalf.</p>
        <h2>Photos and video</h2>
        <p>We only publish photos or videos of participants who have given consent (or whose parent or guardian has, for minors). You may change your choice at any time by contacting us.</p>
        <h2>Children's privacy</h2>
        <p>Registrations for participants under 18 must be completed by a parent or legal guardian.</p>
        <h2>Your choices</h2>
        <p>You may ask us to access, correct, or delete your information, or to remove you from any list, by contacting us <ContactLine />through our <Link to="/contact">contact page</Link>.</p>
        <h2>Changes</h2>
        <p>We may update this policy and will post the new version on this page.</p>
      </div>
    </section>
  );
}

export function Terms() {
  const { t } = useTranslation();
  useSeo({ title: t("legal.termsTitle"), noindex: true });
  return (
    <section className="section">
      <div className="container prose">
        <DraftBanner />
        <h1>{t("legal.termsTitle")}</h1>
        <p><em>Last updated: [DATE — fill in at launch]</em></p>
        <p>By using this website, you agree to these terms.</p>
        <h2>Use of the site</h2>
        <p>Please use this site lawfully and respectfully. Do not attempt to disrupt the site or submit false information.</p>
        <h2>Health and wellness information</h2>
        <p>Content about Tai Chi, Baguazhang, yoga, bodywork, and other wellness activities is general information, not medical advice. Participants should consult their healthcare provider before starting a new exercise program. We do not claim that any practice prevents, treats, or cures any condition.</p>
        <h2>Research</h2>
        <p>Qi Code Academy does not currently conduct research studies. Any future study would be run with qualified research partners under their own ethics review and informed-consent process.</p>
        <h2>Donations</h2>
        <p>Donations are processed securely by Stripe. Monthly gifts continue until you ask us to cancel them. Information about our tax-exempt status is shown on the donation page; please consult your tax advisor regarding deductibility.</p>
        <h2>Content</h2>
        <p>Text, photos, and graphics on this site belong to Qi Code Academy, Inc. or are used with permission, and may not be reused without permission.</p>
        <h2>Links</h2>
        <p>We are not responsible for the content of websites we link to.</p>
        <h2>Changes</h2>
        <p>We may update these terms and will post the new version on this page.</p>
      </div>
    </section>
  );
}
