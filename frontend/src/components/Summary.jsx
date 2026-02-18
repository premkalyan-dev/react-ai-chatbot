import { useEffect, useState } from "react";

function Summary() {

  const [data, setData] = useState({
    patientName: "",
    age: "",
    gender: "",
    reportId: "",
    labRef: "",
    status: ""
  });

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      const params = new URLSearchParams(window.location.search);
      const pid = params.get("pid");
      const rid = params.get("rid");
      const exp = params.get("exp");
      const sig = params.get("sig");

      const response = await fetch(
        `/api/summary?pid=${pid}&rid=${rid}&exp=${exp}&sig=${sig}`
      );

      const result = await response.json();
      setData(result);

    } catch (err) {
      console.log("Error loading summary:", err);
    }
  };

  return (
    <div className="container">

      <div className="card">

        <div className="header">
          <h2>Secure Medical Report</h2>
          <p>Patient: {data.patientName}</p>
        </div>

        <div className="grid">

          <div className="info">
            <label>Patient</label>
            <div>{data.gender}, {data.age}Y</div>
          </div>

          <div className="info">
            <label>Status</label>
            <div>✔ {data.status}</div>
          </div>

          <div className="info">
            <label>Report ID</label>
            <div>{data.reportId}</div>
          </div>

          <div className="info">
            <label>Lab Ref</label>
            <div>{data.labRef}</div>
          </div>

        </div>

      </div>

    </div>
  );
}

export default Summary;
