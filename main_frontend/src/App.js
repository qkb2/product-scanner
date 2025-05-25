// App.js
import React, { useState, useEffect } from "react";

const SERVER_URL = "https://127.0.0.1:8000";

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
  const [devices, setDevices] = useState([]);
  const [deviceSecret, setDeviceSecret] = useState("");

  useEffect(() => {
    fetchIncidents();
    fetchProducts();
    fetchDevices();
    const interval = setInterval(fetchIncidents, 10000);
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

  const fetchDevices = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/get_devices`);
      const data = await res.json();
      setDevices(data);
    } catch (err) {
      console.error("Error fetching devices:", err);
    }
  };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    setMessage("Processing...");

    try {
      const formData = new FormData();
      Object.entries(form).forEach(([key, val]) => formData.append(key, val));

      const res = await fetch(`${SERVER_URL}/add_product`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Unknown error");

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
      if (!res.ok) throw new Error(data.detail || "Unknown error");

      setMessage(data.message);
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  const handleRemoveDevice = async (id) => {
    if (!deviceSecret) {
      alert("Please provide the shared secret.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("device_id", id);
      formData.append("shared_secret", deviceSecret);

      const res = await fetch(`${SERVER_URL}/remove_device`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Unknown error");

      setMessage(data.message);
      fetchDevices();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    }
  };

  return (
    <div className="p-8 font-sans max-w-3xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold text-blue-700">Main Server Dashboard</h1>

      <section>
        <h2 className="text-xl font-semibold mb-2">Last 10 Incidents</h2>
        <ul className="space-y-1 text-gray-700">
          {incidents.map((i, idx) => (
            <li key={idx}>
              [{new Date(i.timestamp).toLocaleString()}] {i.product} - {i.weight}g -{" "}
              <span className="font-semibold">{i.result.toUpperCase()}</span> (Device: {i.device})
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Products</h2>
        <ul className="list-disc pl-6 space-y-1 text-gray-700">
          {products.map((p, idx) => (
            <li key={idx}>
              {p.name} - {p.weight}g
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Add / Update Product</h2>
        <form onSubmit={handleAddProduct} className="space-y-3">
          <input
            type="text"
            placeholder="Name"
            className="w-full p-2 border border-gray-300 rounded"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            type="number"
            placeholder="Weight"
            className="w-full p-2 border border-gray-300 rounded"
            value={form.weight}
            onChange={(e) => setForm({ ...form, weight: e.target.value })}
            required
          />
          <input
            type="number"
            placeholder="Model ID"
            className="w-full p-2 border border-gray-300 rounded"
            value={form.model_id}
            onChange={(e) => setForm({ ...form, model_id: e.target.value })}
            required
          />
          <input
            type="password"
            placeholder="Shared Secret"
            className="w-full p-2 border border-gray-300 rounded"
            value={form.shared_secret}
            onChange={(e) => setForm({ ...form, shared_secret: e.target.value })}
            required
          />
          <button
            type="submit"
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Submit
          </button>
        </form>
        <p className="text-sm mt-2 text-gray-700">{message}</p>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Registered Devices</h2>
        <div className="space-y-2">
          <input
            type="password"
            placeholder="Shared Secret"
            className="w-full p-2 border border-gray-300 rounded"
            value={deviceSecret}
            onChange={(e) => setDeviceSecret(e.target.value)}
          />
          <button
            onClick={fetchDevices}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Refresh Device List
          </button>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            {devices.map((d) => (
              <li key={d.id} className="flex items-center justify-between">
                {d.name}
                <button
                  onClick={() => handleRemoveDevice(d.id)}
                  className="ml-4 px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      </section>


      <section>
        <h2 className="text-xl font-semibold mb-2">Reset Devices</h2>
        <form onSubmit={handleResetDevices} className="space-y-3">
          <input
            type="password"
            placeholder="Shared Secret"
            className="w-full p-2 border border-gray-300 rounded"
            value={resetSecret}
            onChange={(e) => setResetSecret(e.target.value)}
            required
          />
          <button
            type="submit"
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Reset Devices
          </button>
        </form>
      </section>
    </div>
  );
}

export default App;
