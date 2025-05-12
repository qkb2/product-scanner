import React, { useState, useEffect } from "react";

const SERVER_URL = "https://127.0.0.1:8000"; // local server

function App() {
  const [incidents, setIncidents] = useState([]);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({
    name: "",
    weight: "",
    model_id: "",
    shared_secret: "",
  });
  const [message, setMessage] = useState("");
  const [resetSecret, setResetSecret] = useState("");


  useEffect(() => {
    fetchIncidents();
    fetchProducts();
    const interval = setInterval(fetchIncidents, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/incidents/last`);
      const data = await res.json();
      setIncidents(data);
    } catch (err) {
      console.error("Error fetching incidents:", err);
    }
  };

  const fetchProducts = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/get_products`);
      const data = await res.json();
      setProducts(data);
    } catch (err) {
      console.error("Error fetching products:", err);
    }
  };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    setMessage("Processing...");

    try {
      const formData = new FormData();
      formData.append("name", form.name);
      formData.append("weight", form.weight);
      formData.append("model_id", form.model_id);
      formData.append("shared_secret", form.shared_secret);

      const res = await fetch(`${SERVER_URL}/add_product`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Unknown error");
      }

      setMessage(data.message);
      fetchProducts();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  const handleResetDevices = async (e) => {
    e.preventDefault();
    setMessage("Resetting devices...");

    try {
      const formData = new FormData();
      formData.append("shared_secret", resetSecret);

      const res = await fetch(`${SERVER_URL}/reset_devices`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Unknown error");
      }

      setMessage(data.message);
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>Main Server Dashboard</h1>

      <section>
        <h2>Last 10 Incidents</h2>
        <ul>
          {incidents.map((i, idx) => (
            <li key={idx}>
              [{new Date(i.timestamp).toLocaleString()}] {i.product} - {i.weight}g -{" "}
              {i.result.toUpperCase()} (Device: {i.device})
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Products</h2>
        <ul>
          {products.map((p, idx) => (
            <li key={idx}>
              {p.name} - {p.weight}g
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Add / Update Product</h2>
        <form onSubmit={handleAddProduct}>
          <input
            type="text"
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            type="number"
            placeholder="Weight"
            value={form.weight}
            onChange={(e) => setForm({ ...form, weight: e.target.value })}
            required
          />
          <input
            type="number"
            placeholder="Model ID"
            value={form.model_id}
            onChange={(e) => setForm({ ...form, model_id: e.target.value })}
            required
          />
          <input
            type="password"
            placeholder="Shared Secret"
            value={form.shared_secret}
            onChange={(e) => setForm({ ...form, shared_secret: e.target.value })}
            required
          />
          <button type="submit">Submit</button>
        </form>
        <p>{message}</p>
      </section>

      <section>
        <h2>Reset Devices</h2>
        <form onSubmit={handleResetDevices}>
          <input
            type="password"
            placeholder="Shared Secret"
            value={resetSecret}
            onChange={(e) => setResetSecret(e.target.value)}
            required
          />
          <button type="submit">Reset Devices</button>
        </form>
      </section>

    </div>
  );
}

export default App;
