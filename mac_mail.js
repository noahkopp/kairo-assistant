// Kairo <-> the Mac Mail app (e.g. the school Outlook/Exchange account). Prints JSON.
// osascript -l JavaScript mac_mail.js ACTION '{json args}'
function run(argv) {
  const action = argv[0];
  const a = argv[1] ? JSON.parse(argv[1]) : {};
  const Mail = Application('Mail');
  const out = (x) => JSON.stringify(x);

  function inboxes(account) {
    if (!account) return [Mail.inbox];
    const acct = Mail.accounts.whose({ name: { _contains: account } })()[0];
    if (!acct) throw new Error('No Mail account matching "' + account + '". Accounts: ' + Mail.accounts.name().join(', '));
    return acct.mailboxes.whose({ _or: [{ name: 'INBOX' }, { name: 'Inbox' }] })();
  }
  function findMessage(id) {
    const m = Mail.inbox.messages.whose({ id: Number(id) })();
    if (!m.length) throw new Error('No inbox message with id ' + id);
    return m[0];
  }

  if (action === 'accounts') {
    return out(Mail.accounts().map(x => ({ name: x.name(), emails: x.emailAddresses(), enabled: x.enabled() })));
  }
  if (action === 'list') {
    const limit = Math.min(a.max_results || 10, 50);
    let rows = [];
    for (const box of inboxes(a.account || '')) {
      const msgs = a.unread_only ? box.messages.whose({ readStatus: false }) : box.messages;
      const ids = msgs.id(), subj = msgs.subject(), from = msgs.sender(), dates = msgs.dateReceived(), read = msgs.readStatus();
      for (let i = 0; i < ids.length; i++) {
        rows.push({ id: String(ids[i]), from: from[i], subject: subj[i], date: dates[i], unread: !read[i] });
      }
    }
    rows.sort((x, y) => new Date(y.date) - new Date(x.date));
    return out(rows.slice(0, limit));
  }
  if (action === 'read') {
    const m = findMessage(a.email_id);
    let body = m.content() || '';
    if (body.length > 8000) body = body.slice(0, 8000) + '\n...(truncated)';
    return out({ id: a.email_id, from: m.sender(), to: m.toRecipients.address(), subject: m.subject(),
                 date: m.dateReceived(), body: body });
  }
  if (action === 'mark_read' || action === 'mark_unread') {
    const val = action === 'mark_read';
    let count = 0;
    if (a.email_ids) {
      for (const id of a.email_ids) { findMessage(id).readStatus = val; count++; }
    } else if (a.all_unread && val) {
      for (const box of inboxes(a.account || '')) {
        const msgs = box.messages.whose({ readStatus: false })();
        for (const m of msgs) { m.readStatus = true; count++; }
      }
    }
    return out({ changed: count });
  }
  if (action === 'draft' || action === 'send') {
    const msg = Mail.OutgoingMessage({ subject: a.subject || '', content: a.body || '',
                                       visible: action === 'draft' });
    Mail.outgoingMessages.push(msg);
    for (const addr of String(a.to).split(',')) {
      msg.toRecipients.push(Mail.Recipient({ address: addr.trim() }));
    }
    if (a.account) {
      const acct = Mail.accounts.whose({ name: { _contains: a.account } })()[0];
      if (acct) msg.sender = acct.emailAddresses()[0];
    }
    if (action === 'send') { msg.send(); return out({ sent: true }); }
    Mail.activate();
    return out({ draft_opened_in_mail: true });
  }
  throw new Error('Unknown action ' + action);
}
