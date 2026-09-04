document.addEventListener("DOMContentLoaded", function () {

    const billDate = document.getElementById("billDate");

    if (billDate) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, "0");
        const day = String(today.getDate()).padStart(2, "0");

        billDate.value = `${year}-${month}-${day}`;
    }

    calculateBill();
});


function getNumber(value) {

    const number = parseFloat(value);

    if (isNaN(number)) {
        return 0;
    }

    return number;
}


function calculateBill() {

    const rows = document.querySelectorAll("#billItems tr");

    let subtotal = 0;

    rows.forEach(function (row) {

        const netWeightInput = row.querySelector(".net-weight");
        const rateInput = row.querySelector(".rate");
        const makingInput = row.querySelector(".making");
        const amountCell = row.querySelector(".row-amount");

        if (!netWeightInput || !rateInput || !makingInput || !amountCell) {
            return;
        }

        const netWeight = getNumber(netWeightInput.value);
        const rate = getNumber(rateInput.value);
        const making = getNumber(makingInput.value);

        const goldValue = netWeight * rate;
        const amount = goldValue + making;

        subtotal += amount;

        amountCell.innerText = "₹" + amount.toFixed(2);
        amountCell.dataset.amount = amount.toFixed(2);
    });


    const discountInput = document.getElementById("discount");

    const discount = discountInput
        ? getNumber(discountInput.value)
        : 0;


    let taxableAmount = subtotal - discount;

    if (taxableAmount < 0) {
        taxableAmount = 0;
    }


    const gst = taxableAmount * 0.03;

    const grandTotal = taxableAmount + gst;


    document.getElementById("subtotal").innerText =
        subtotal.toFixed(2);

    document.getElementById("gst").innerText =
        gst.toFixed(2);

    document.getElementById("grandTotal").innerText =
        grandTotal.toFixed(2);


    calculateBalance();
}


function calculateBalance() {

    const grandTotal =
        getNumber(
            document.getElementById("grandTotal").innerText
        );

    const amountPaid =
        getNumber(
            document.getElementById("amountPaid").value
        );

    let balance = grandTotal - amountPaid;

    if (balance < 0) {
        balance = 0;
    }

    document.getElementById("balanceDue").innerText =
        balance.toFixed(2);
}


function addItem() {

    const tbody = document.getElementById("billItems");

    const row = document.createElement("tr");

    row.innerHTML = `

        <td>
            <input
                type="text"
                class="item-name"
                placeholder="Item Name"
            >
        </td>

        <td>

            <select class="purity">

                <option value="22K">
                    22K
                </option>

                <option value="18K">
                    18K
                </option>

                <option value="24K">
                    24K
                </option>

                <option value="Silver">
                    Silver
                </option>

            </select>

        </td>

        <td>

            <input
                type="number"
                class="gross-weight"
                step="0.001"
                min="0"
                placeholder="Optional"
            >

        </td>

        <td>

            <input
                type="number"
                class="net-weight"
                step="0.001"
                min="0"
                placeholder="0.000"
                oninput="calculateBill()"
            >

        </td>

        <td>

            <input
                type="number"
                class="rate"
                step="0.01"
                min="0"
                placeholder="₹ Rate"
                oninput="calculateBill()"
            >

        </td>

        <td>

            <input
                type="number"
                class="making"
                step="0.01"
                min="0"
                value="0"
                placeholder="₹ Making"
                oninput="calculateBill()"
            >

        </td>

        <td class="row-amount">
            ₹0.00
        </td>

    `;

    tbody.appendChild(row);
}


async function saveBill() {

    calculateBill();


    const customerName =
        document.getElementById("customerName").value.trim();

    const customerMobile =
        document.getElementById("customerMobile").value.trim();

    const billNo =
        document.getElementById("billNo").value.trim();


    if (!customerName) {

        alert("Customer Name enter kariye.");

        document.getElementById("customerName").focus();

        return;
    }


    const items = [];

    const rows =
        document.querySelectorAll("#billItems tr");


    rows.forEach(function (row) {

        const itemNameInput =
            row.querySelector(".item-name");

        const purityInput =
            row.querySelector(".purity");

        const grossInput =
            row.querySelector(".gross-weight");

        const netInput =
            row.querySelector(".net-weight");

        const rateInput =
            row.querySelector(".rate");

        const makingInput =
            row.querySelector(".making");

        const amountCell =
            row.querySelector(".row-amount");


        if (!itemNameInput) {
            return;
        }


        const itemName =
            itemNameInput.value.trim();


        if (!itemName) {
            return;
        }


        /*
            IMPORTANT:
            Gross Weight optional hai.

            Agar blank hai to database me 0 jayega.
        */

        const grossWeight =
            grossInput && grossInput.value.trim() !== ""
                ? getNumber(grossInput.value)
                : 0;


        const item = {

            item_name:
                itemName,

            purity:
                purityInput
                    ? purityInput.value
                    : "",

            gross_weight:
                grossWeight,

            net_weight:
                netInput
                    ? getNumber(netInput.value)
                    : 0,

            rate:
                rateInput
                    ? getNumber(rateInput.value)
                    : 0,

            making:
                makingInput
                    ? getNumber(makingInput.value)
                    : 0,

            amount:
                amountCell
                    ? getNumber(amountCell.dataset.amount)
                    : 0
        };


        items.push(item);
    });


    if (items.length === 0) {

        alert("Kam se kam ek jewellery item enter kariye.");

        return;
    }


    const subtotal =
        getNumber(
            document.getElementById("subtotal").innerText
        );

    const discount =
        getNumber(
            document.getElementById("discount").value
        );

    const gst =
        getNumber(
            document.getElementById("gst").innerText
        );

    const grandTotal =
        getNumber(
            document.getElementById("grandTotal").innerText
        );

    const amountPaid =
        getNumber(
            document.getElementById("amountPaid").value
        );

    const paymentMode =
        document.getElementById("paymentMode").value;


    if (amountPaid > grandTotal) {

        alert(
            "Amount Paid Grand Total se jyada nahi ho sakta."
        );

        return;
    }


    const billData = {

        bill_no:
            billNo,

        customer_name:
            customerName,

        customer_mobile:
            customerMobile,

        subtotal:
            subtotal,

        discount:
            discount,

        gst:
            gst,

        grand_total:
            grandTotal,

        payment_mode:
            paymentMode,

        amount_paid:
            amountPaid,

        items:
            items
    };


    try {

        const response =
            await fetch(
                "/save_bill",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(billData)
                }
            );


        const result =
            await response.json();


        if (result.success) {

            alert(
                "Bill Saved Successfully! ✅"
            );

            /*
                Save hone ke baad direct
                final invoice khulega.
            */

            window.location.href =
                "/bill/" + result.bill_id;

        }

        else {

            alert(
                result.message ||
                "Bill save nahi hua."
            );
        }

    }

    catch (error) {

        console.error(error);

        alert(
            "Bill save karte waqt error aaya."
        );
    }
}


function newBill() {

    const confirmNew =
        confirm(
            "Naya bill start karna hai?"
        );

    if (confirmNew) {

        window.location.href =
            "/new-bill";
    }
}