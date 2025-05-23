// App.js
import React, { useEffect, useState } from "react";

const BACKEND = process.env.REACT_APP_BACKEND;

function App() {
  const [weight, setWeight] = useState(0.0);
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [responseMsg, setResponseMsg] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${BACKEND}/weight`)
        .then(res => res.json())
        .then(data => setWeight(data.current_weight))
        .catch(console.error);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchProducts = () => {
    fetch(`${BACKEND}/get_products`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "error") {
          alert("Error fetching products: " + data.details);
        } else {
          setProducts(data.products);
        }
      })
      .catch(console.error);
  };

  useEffect(() => {
    fetchProducts();
    const interval = setInterval(fetchProducts, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const sendProduct = () => {
    if (!selectedProductId) {
      alert("Please select a product");
      return;
    }

    fetch(`${BACKEND}/send_product`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: selectedProductId }),
    })
      .then(res => res.json())
      .then(data => {
        setResponseMsg(data.status === "correct" ? "✅ OK" : "❌ Not OK, wait for staff");
      })
      .catch(err => setResponseMsg("❌ Error: " + err.message));
  };

  return (
    <div className="p-6 font-sans max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-blue-700">Weigh a Product</h1>
      <div className="text-lg">Current weight: <strong>{weight} g</strong></div>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Products List</h2>
        <button
          onClick={fetchProducts}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh Products
        </button>

        <select
          value={selectedProductId}
          onChange={e => setSelectedProductId(e.target.value)}
          className="w-full border border-gray-300 p-2 rounded mt-2"
        >
          <option value="">Select a product</option>
          {products.map(product => (
            <option key={product.id} value={product.id}>
              {product.name} - {product.weight} g
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <button
          onClick={sendProduct}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Send to Server
        </button>
        <p className="text-md">{responseMsg}</p>
      </div>
    </div>
  );
}

export default App;
