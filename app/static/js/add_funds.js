function addMoney() {
  // Show modal
  const modal = document.getElementById("addMoneyModal");
  const phone = document.getElementById("mpesaNumber").textContent.trim();
  
  // Display user's default M-Pesa number
  document.getElementById("mpesaDisplay").textContent = 
    `M-Pesa Phone: ${phone}`;
    
  modal.style.display = "flex";
}

function closeAddMoneyModal() {
  document.getElementById("addMoneyModal").style.display = "none";
  document.getElementById("topupAmount").value = "";
  document.getElementById("topupStatus").style.display = "none";
}

async function submitTopup() {
  const amount = document.getElementById("topupAmount").value;
  const phone = document.getElementById("mpesaNumber").textContent.trim();
  const status = document.getElementById("topupStatus");

  if (!amount || amount < 50) {
    status.textContent = "Minimum top-up is KSh 50.";
    status.style.display = "block";
    status.style.color = "red";
    return;
  }

  status.textContent = "Initiating payment...";
  status.style.display = "block";
  status.style.color = "blue";

  try {
    const res = await fetch("/api/mpesa/stk-push", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({phone, amount})
    });

    const data = await res.json();

    if (res.ok && data.ResponseCode === "0") {
      status.textContent = "✅ Check your M-Pesa for the payment prompt!";
      status.style.color = "green";
    } else {
      status.textContent = data.errorMessage || "Payment request failed.";
      status.style.color = "red";
    }
  } catch (err) {
    console.error("Payment error:", err);
    status.textContent = "Network error. Please try again.";
    status.style.color = "red";
  }
}