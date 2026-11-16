/**
 * Server-side spam guard for the contact-form Apps Script endpoint.
 *
 * The page (contact.html) already filters bots in the browser, but a bot that
 * POSTs straight to the Apps Script URL skips those checks. This file repeats
 * them on the server. It is NOT deployed automatically: paste it into the Apps
 * Script project that receives the form (the one in contact.html's `action`),
 * then add two lines at the top of the existing doPost(e) — see INSTALL below.
 *
 * INSTALL
 *   1. Open the Apps Script project, add a new file "spam-guard", paste this.
 *   2. At the very top of the existing doPost(e), add:
 *
 *        var guard = checkSpam_(e);
 *        if (guard.drop) { return <the same response doPost returns on success>; }
 *
 *      and where the script builds the email subject, prefix it when flagged:
 *
 *        if (guard.flag) { subject = '[Unverified] ' + subject; }
 *
 *   3. Deploy > Manage deployments > edit the current deployment > New version.
 *      Keep the same deployment so the URL in contact.html does not change.
 *
 * WHAT IT DOES
 *   drop (silently discarded, bot sees the normal success response):
 *     - the hidden honeypot field "website" is filled
 *     - the Name contains a link or 5+ digits in a row (the Oct 2026 spam)
 *   flag (still delivered, subject marked "[Unverified]"):
 *     - js_ok is missing, i.e. the post did not come through the page script.
 *       Direct-POST bots land here; so would a rare visitor with JavaScript
 *       off, which is why these are flagged rather than dropped.
 */

var SPAM_NAME_ = /(https?:|:\/\/|www\.|\.buzz\b|\d{5,})/i;

function parseFormFields_(e) {
  var p = {};
  if (e && e.parameter) {
    for (var k in e.parameter) p[k] = String(e.parameter[k]);
  }
  // contact.html posts enctype="text/plain": "key=value" per line.
  if (e && e.postData && e.postData.contents && /text\/plain/i.test(e.postData.type || '')) {
    e.postData.contents.split(/\r?\n/).forEach(function (line) {
      var i = line.indexOf('=');
      if (i > 0) {
        var key = line.slice(0, i).trim();
        if (!(key in p)) p[key] = line.slice(i + 1);
      }
    });
  }
  return p;
}

function checkSpam_(e) {
  var p = parseFormFields_(e);
  var name = (p.name || '').trim();
  if ((p.website || '').trim() !== '') return { drop: true, flag: false, reason: 'honeypot' };
  if (SPAM_NAME_.test(name)) return { drop: true, flag: false, reason: 'name pattern' };
  if (p.js_ok !== '1') return { drop: false, flag: true, reason: 'no js_ok' };
  return { drop: false, flag: false, reason: '' };
}
