const editBtn = document.getElementById("edit-product");
const error = document.getElementById("error");
const buyBtn = document.getElementById("buy-now");

// get current productID from URL
const re = new RegExp(
    "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
);
const productID = window.location.href.match(re)[0];

// if edit button is displayed
if (!!editBtn) {
    editBtn.href = `/admin/updateProduct/${productID}`;
}

// if buy button is displayed
if (!!buyBtn) {
    buyBtn.addEventListener("click", async (e) => makePurchase(e));

    const makePurchase = async (e) => {
        e.preventDefault();
        const response = await (
            await fetch(`/purchase/${productID}`)
        ).statusText;
        console.log(response);
    };
}
