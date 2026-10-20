/**
 * Support the developer: one UPI QR and a copyable UPI ID. Any UPI app works
 * (the QR is plain UPI, not tied to one payment app). Nothing here is tracked.
 */
const SupportPage = (() => {
  const UPI_ID = 'krisp@ybl';
  const COPIED_RESET_MS = 2000;

  function render(container) {
    container.innerHTML = `
      <section class="support">
        <div class="support-card">
          <h1 class="support-title">Support the developer</h1>
          <p class="support-lead">Boltools is free, offline and made by one person. If it saved you time, a small UPI tip keeps new tools coming.</p>
          <div class="support-qr">
            <img src="assets/support_upi_qr.svg" alt="UPI QR code for ${escapeAttr(UPI_ID)}" width="232" height="232">
          </div>
          <p class="support-hint">Scan with any UPI app: Google Pay, PhonePe, Paytm or your bank app.</p>
          <div class="support-upi">
            <code class="support-upi-id">${escapeHtml(UPI_ID)}</code>
            <button type="button" class="support-copy" data-support-copy>Copy UPI ID</button>
          </div>
          <p class="support-note">Every tool stays free whether you tip or not.</p>
        </div>
      </section>`;
    container.querySelector('[data-support-copy]').addEventListener('click', copyUpiId);
  }

  async function copyUpiId(event) {
    const button = event.currentTarget;
    try {
      await navigator.clipboard.writeText(UPI_ID);
      button.textContent = 'Copied';
    } catch (err) {
      showToast(`Copy failed. The UPI ID is ${UPI_ID}`, 'error');
      return;
    }
    setTimeout(() => { button.textContent = 'Copy UPI ID'; }, COPIED_RESET_MS);
  }

  return { render };
})();
