import React, { useEffect, useState } from "react";

const BACKEND = process.env.REACT_APP_BACKEND;

function App() {
  const [weight, setWeight] = useState(0.0);
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState("");
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
    if (!selectedProduct) {
      alert("Please select a product");
      return;
    }

    fetch(`${BACKEND}/send_product`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product: selectedProduct }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "correct") {
          setResponseMsg("✅ OK");
        } else {
          setResponseMsg("❌ Not OK, wait for staff");
        }
      })
      .catch(err => {
        setResponseMsg("❌ Error: " + err.message);
      });
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h1>Weigh a Product</h1>
      <p>Current weight: <strong>{weight} g</strong></p>

      <h2>Products List</h2>
      <button onClick={fetchProducts}>Get Products</button>
      <br /><br />

      <select value={selectedProduct} onChange={e => setSelectedProduct(e.target.value)}>
        <option value="">Select a product</option>
        {products.map((product, index) => (
          <option key={index} value={product.name}>
            {product.name} - {product.weight} g
          </option>
        ))}
      </select>

      <br /><br />
      <button onClick={sendProduct}>Send to Server</button>
      <p>{responseMsg}</p>
    </div>
  );
}

export default App;
