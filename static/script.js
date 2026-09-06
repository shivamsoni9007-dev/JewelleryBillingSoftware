// =====================================================
// DATE
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    const dateField =
        document.getElementById("bill_date");

    if (dateField) {

        const today = new Date();

        const yyyy = today.getFullYear();

        const mm =
            String(today.getMonth() + 1)
                .padStart(2, "0");

        const dd =
            String(today.getDate())
                .padStart(2, "0");

        dateField.value =
            `${yyyy}-${mm}-${dd}`;
    }

    updateAllGoldRates();

    calculateBillTotal();
});


// =====================================================
// GOLD RATE FROM 24K
// =====================================================

function getGoldRateByPurity(purity) {

    const gold24Rate =
        parseFloat(
            document.getElementById("gold_24k_rate")?.value
        ) || 0;


    const karatMap = {

        "24K": 24,
        "22K": 22,
        "21K": 21,
        "20K": 20,
        "18K": 18

    };


    const karat =
        karatMap[purity];


    if (!karat || gold24Rate <= 0) {

        return 0;

    }


    return gold24Rate * karat / 24;
}


// =====================================================
// UPDATE GOLD RATE PREVIEW + ALL GOLD ROWS
// =====================================================

function updateAllGoldRates() {

    const purities =
        ["24K", "22K", "21K", "20K", "18K"];


    purities.forEach(function (purity) {

        const rate =
            getGoldRateByPurity(purity);


        const preview =
            document.getElementById(
                "preview_" + purity.toLowerCase()
            );


        if (preview) {

            preview.textContent =
                "₹" + rate.toFixed(2);

        }

    });


    document
        .querySelectorAll(".item-row")
        .forEach(function (row) {

            const metal =
                row.querySelector(".metal")?.value;


            if (metal === "Gold") {

                calculateRow(row);

            }

        });
}


// =====================================================
// METAL CHANGE
// =====================================================

function metalChanged(selectElement) {

    const row =
        selectElement.closest("tr");

    const purity =
        row.querySelector(".purity");

    const rateField =
        row.querySelector(".rate");

    const metal =
        selectElement.value;


    purity.innerHTML = "";


    if (metal === "Silver") {

        purity.innerHTML = `

            <option value="100%">
                Silver 100%
            </option>

            <option value="95%">
                Silver 95%
            </option>

            <option value="90%">
                Silver 90%
            </option>

        `;


        if (rateField) {

            rateField.readOnly = false;

            rateField.value = "";

            rateField.placeholder =
                "₹ / gram";

            rateField.classList.remove(
                "gold-auto-rate"
            );

        }

    }

    else {

        purity.innerHTML = `

            <option value="24K">
                Gold 24K
            </option>

            <option value="22K" selected>
                Gold 22K
            </option>

            <option value="21K">
                Gold 21K
            </option>

            <option value="20K">
                Gold 20K
            </option>

            <option value="18K">
                Gold 18K
            </option>

        `;


        if (rateField) {

            rateField.readOnly = true;

            rateField.placeholder =
                "Auto Rate";

            rateField.classList.add(
                "gold-auto-rate"
            );

        }

    }


    calculateRow(row);
}


// =====================================================
// CALCULATE SINGLE ITEM
// =====================================================

function calculateRow(row) {

    const metal =
        row.querySelector(".metal")?.value || "Gold";

    const purity =
        row.querySelector(".purity")?.value || "";

    const netWeight =
        parseFloat(
            row.querySelector(".net-weight")?.value
        ) || 0;

    const makingPerGram =
        parseFloat(
            row.querySelector(".making")?.value
        ) || 0;

    const rateField =
        row.querySelector(".rate");


    let rate = 0;

    let purityMultiplier = 1;


    // ============================================
    // GOLD RATE
    // ============================================

    if (metal === "Gold") {

        rate =
            getGoldRateByPurity(purity);


        if (rateField) {

            rateField.value =
                rate > 0
                    ? rate.toFixed(2)
                    : "";

        }

    }


    // ============================================
    // SILVER RATE + PURITY
    // ============================================

    else if (metal === "Silver") {

        rate =
            parseFloat(
                rateField?.value
            ) || 0;


        if (purity === "100%") {

            purityMultiplier = 1;

        }

        else if (purity === "95%") {

            purityMultiplier = 0.95;

        }

        else if (purity === "90%") {

            purityMultiplier = 0.90;

        }

    }


    // ============================================
    // METAL AMOUNT
    // ============================================

    const metalAmount =
        netWeight *
        rate *
        purityMultiplier;


    // ============================================
    // MAKING PER GRAM
    // ============================================

    const makingAmount =
        netWeight *
        makingPerGram;


    // ============================================
    // ITEM TOTAL
    // ============================================

    const itemTotal =
        metalAmount +
        makingAmount;


    const amountField =
        row.querySelector(".amount");


    if (amountField) {

        amountField.value =
            itemTotal.toFixed(2);

    }


    calculateBillTotal();
}


// =====================================================
// BILL TOTAL
// =====================================================

function calculateBillTotal() {

    let subtotal = 0;


    document
        .querySelectorAll(".amount")
        .forEach(function (field) {

            subtotal +=
                parseFloat(field.value) || 0;

        });


    const discount =
        parseFloat(
            document.getElementById("discount")?.value
        ) || 0;


    const gstPercent =
        parseFloat(
            document.getElementById("gst_percent")?.value
        ) || 0;


    let taxableAmount =
        subtotal - discount;


    if (taxableAmount < 0) {

        taxableAmount = 0;

    }


    const gstAmount =
        taxableAmount *
        gstPercent /
        100;


    const grandTotal =
        taxableAmount +
        gstAmount;


    const subtotalField =
        document.getElementById("subtotal");

    const gstField =
        document.getElementById("gst");

    const grandTotalField =
        document.getElementById("grand_total");


    if (subtotalField) {

        subtotalField.value =
            subtotal.toFixed(2);

    }


    if (gstField) {

        gstField.value =
            gstAmount.toFixed(2);

    }


    if (grandTotalField) {

        grandTotalField.value =
            grandTotal.toFixed(2);

    }


    calculateBalance();
}


// =====================================================
// BALANCE
// =====================================================

function calculateBalance() {

    const grandTotal =
        parseFloat(
            document.getElementById("grand_total")?.value
        ) || 0;


    const amountPaid =
        parseFloat(
            document.getElementById("amount_paid")?.value
        ) || 0;


    let balance =
        grandTotal - amountPaid;


    if (balance < 0) {

        balance = 0;

    }


    const balanceField =
        document.getElementById("balance");


    if (balanceField) {

        balanceField.value =
            balance.toFixed(2);

    }
}


// =====================================================
// ADD NEW ITEM ROW
// =====================================================

function addRow() {

    const body =
        document.getElementById("itemsBody");


    const row =
        document.createElement("tr");


    row.className = "item-row";


    row.innerHTML = `

        <td>

            <input
                type="text"
                class="item-name"
                placeholder="Ring / Chain"
            >

        </td>


        <td>

            <select
                class="metal"
                onchange="metalChanged(this)"
            >

                <option value="Gold">
                    Gold
                </option>

                <option value="Silver">
                    Silver
                </option>

            </select>

        </td>


        <td>

            <select
                class="purity"
                onchange="calculateRow(this.closest('tr'))"
            >

                <option value="24K">
                    Gold 24K
                </option>

                <option value="22K" selected>
                    Gold 22K
                </option>

                <option value="21K">
                    Gold 21K
                </option>

                <option value="20K">
                    Gold 20K
                </option>

                <option value="18K">
                    Gold 18K
                </option>

            </select>

        </td>


        <td>

            <input
                type="number"
                class="gross-weight"
                placeholder="Optional"
                step="0.001"
                min="0"
            >

        </td>


        <td>

            <input
                type="number"
                class="net-weight"
                placeholder="0.000"
                step="0.001"
                min="0"
                oninput="calculateRow(this.closest('tr'))"
            >

        </td>


        <td>

            <input
                type="number"
                class="rate gold-auto-rate"
                placeholder="Auto Rate"
                step="0.01"
                min="0"
                readonly
            >

        </td>


        <td>

            <input
                type="number"
                class="making"
                placeholder="₹ / gram"
                step="0.01"
                min="0"
                oninput="calculateRow(this.closest('tr'))"
            >

        </td>


        <td>

            <input
                type="number"
                class="amount"
                value="0.00"
                readonly
            >

        </td>


        <td>

            <button
                type="button"
                class="remove-btn"
                onclick="removeRow(this)"
            >
                ✕
            </button>

        </td>

    `;


    body.appendChild(row);


    calculateRow(row);
}


// =====================================================
// REMOVE ITEM
// =====================================================

function removeRow(button) {

    const rows =
        document.querySelectorAll(".item-row");


    if (rows.length <= 1) {

        alert(
            "Kam se kam ek jewellery item hona chahiye."
        );

        return;

    }


    button
        .closest("tr")
        .remove();


    calculateBillTotal();
}


// =====================================================
// SAVE BILL
// =====================================================

async function saveBill() {

    const billNo =
        document
            .getElementById("bill_no")
            .value
            .trim();


    const customerName =
        document
            .getElementById("customer_name")
            .value
            .trim();


    const customerMobile =
        document
            .getElementById("customer_mobile")
            .value
            .trim();


    if (!customerName) {

        alert(
            "Customer Name enter kariye."
        );

        return;

    }


    const goldRows =
        Array.from(
            document.querySelectorAll(".item-row")
        ).filter(function (row) {

            return (
                row.querySelector(".metal")?.value === "Gold" &&
                row.querySelector(".item-name")?.value.trim() !== ""
            );

        });


    const gold24Rate =
        parseFloat(
            document.getElementById("gold_24k_rate")?.value
        ) || 0;


    if (goldRows.length > 0 && gold24Rate <= 0) {

        alert(
            "Gold item ke liye 24K Gold Rate enter kariye."
        );

        return;

    }


    // ===============================================
    // ITEMS
    // ===============================================

    const items = [];


    document
        .querySelectorAll(".item-row")
        .forEach(function (row) {


            const itemName =
                row
                    .querySelector(".item-name")
                    .value
                    .trim();


            if (!itemName) {

                return;

            }


            const metal =
                row.querySelector(".metal").value;


            const purityValue =
                row.querySelector(".purity").value;


            let savedPurity =
                purityValue;


            if (metal === "Silver") {

                savedPurity =
                    "Silver " +
                    purityValue;

            }


            items.push({

                item_name:
                    itemName,

                purity:
                    savedPurity,

                gross_weight:
                    parseFloat(
                        row.querySelector(".gross-weight").value
                    ) || 0,

                net_weight:
                    parseFloat(
                        row.querySelector(".net-weight").value
                    ) || 0,

                rate:
                    parseFloat(
                        row.querySelector(".rate").value
                    ) || 0,

                making:
                    parseFloat(
                        row.querySelector(".making").value
                    ) || 0,

                amount:
                    parseFloat(
                        row.querySelector(".amount").value
                    ) || 0

            });

        });


    if (items.length === 0) {

        alert(
            "Kam se kam ek item enter kariye."
        );

        return;

    }


    // ===============================================
    // TOTALS
    // ===============================================

    const subtotal =
        parseFloat(
            document.getElementById("subtotal").value
        ) || 0;


    const discount =
        parseFloat(
            document.getElementById("discount").value
        ) || 0;


    const gst =
        parseFloat(
            document.getElementById("gst").value
        ) || 0;


    const grandTotal =
        parseFloat(
            document.getElementById("grand_total").value
        ) || 0;


    const amountPaid =
        parseFloat(
            document.getElementById("amount_paid").value
        ) || 0;


    if (amountPaid > grandTotal) {

        alert(
            "Amount Paid Grand Total se jyada nahi ho sakta."
        );

        return;

    }


    const paymentMode =
        document.getElementById("payment_mode").value;


    // ===============================================
    // JSON
    // ===============================================

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


    // ===============================================
    // SEND
    // ===============================================

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
                        JSON.stringify(
                            billData
                        )
                }
            );


        const result =
            await response.json();


        if (result.success) {

            alert(
                "Bill Saved Successfully! ✅"
            );


            window.location.href =
                "/bill/" +
                result.bill_id;

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
            "Server se connection nahi ho pa raha."
        );

    }
}