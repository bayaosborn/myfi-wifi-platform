function manualAddMoney() {
  // Show manual payment modal
  const modal = document.getElementById("manualPaymentModal");
  const phone = document.getElementById("mpesaNumber").textContent.trim();
  
  // Display user's phone
  document.getElementById("manualPhoneDisplay").textContent = `Your phone: ${phone}`;
  
  modal.style.display = "flex";
}

function closeManualPaymentModal() {
  document.getElementById("manualPaymentModal").style.display = "none";
  document.getElementById("manualAmount").value = "";
  document.getElementById("manualMpesaCode").value = "";
  document.getElementById("manualStatus").style.display = "none";
}

async function submitManualPayment() {
  const amount = document.getElementById("manualAmount").value;
  const mpesaCode = document.getElementById("manualMpesaCode").value.toUpperCase();
  const phone = document.getElementById("mpesaNumber").textContent.trim();
  const status = document.getElementById("manualStatus");

  // Validation
  if (!amount || amount < 50) {
    status.textContent = "Minimum payment is KSh 50.";
    status.style.display = "block";
    status.style.color = "red";
    return;
  }

  if (!mpesaCode || mpesaCode.length < 8) {
    status.textContent = "Please enter valid M-Pesa code (e.g. SH12ABC3XY).";
    status.style.display = "block";
    status.style.color = "red";
    return;
  }

  status.textContent = "Submitting payment...";
  status.style.display = "block";
  status.style.color = "blue";

  try {
    const res = await fetch("/api/manual-payment/submit", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        phone: phone,
        amount: parseInt(amount),
        mpesa_code: mpesaCode
      })
    });

    const data = await res.json();

    if (res.ok) {
      status.textContent = "✅ Payment submitted! Awaiting admin approval.";
      status.style.color = "green";
      
      // Clear inputs
      document.getElementById("manualAmount").value = "";
      document.getElementById("manualMpesaCode").value = "";
      
      // Close modal after 3 seconds
      setTimeout(() => {
        closeManualPaymentModal();
      }, 3000);
    } else {
      status.textContent = data.message || "Submission failed.";
      status.style.color = "red";
    }
  } catch (err) {
    console.error("Error:", err);
    status.textContent = "Network error. Please try again.";
    status.style.color = "red";
  }
}

// Auto-uppercase M-Pesa code
document.addEventListener('DOMContentLoaded', function() {
  const codeInput = document.getElementById('manualMpesaCode');
  if (codeInput) {
    codeInput.addEventListener('input', (e) => {
      e.target.value = e.target.value.toUpperCase();
    });
  }
});