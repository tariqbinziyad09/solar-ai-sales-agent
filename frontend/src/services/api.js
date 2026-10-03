import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  timeout: 10000,
});

/*
|--------------------------------------------------------------------------
| REQUEST INTERCEPTOR
|--------------------------------------------------------------------------
| Protected API request se pehle JWT token automatically attach hota hai.
|--------------------------------------------------------------------------
*/
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("solar_crm_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/*
|--------------------------------------------------------------------------
| RESPONSE INTERCEPTOR
|--------------------------------------------------------------------------
| Token invalid/expired ho to session clear karke login par redirect.
|--------------------------------------------------------------------------
*/
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes("/auth/login")
    ) {
      localStorage.removeItem("solar_crm_token");
      localStorage.removeItem("solar_crm_user");

      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

/*
|--------------------------------------------------------------------------
| AUTHENTICATED PROPOSAL PDF DOWNLOAD
|--------------------------------------------------------------------------
| Direct window.open() Authorization header nahi bhejta.
|
| Isliye PDF Axios ke through Blob ki form mein fetch hoti hai.
| Axios interceptor JWT automatically attach kar deta hai.
|--------------------------------------------------------------------------
*/
export async function downloadAuthenticatedFile(
  fileUrl,
  filename = "download.pdf"
) {
  if (!fileUrl) {
    throw new Error("File URL is missing.");
  }

  let requestUrl = fileUrl;

  // Backend kabhi complete URL return kar sakta hai:
  // http://127.0.0.1:8000/api/proposals/15/pdf
  //
  // api Axios instance ka baseURL already:
  // http://127.0.0.1:8000/api
  //
  // Isliye same backend ki /api path ko Axios-friendly
  // relative endpoint mein convert kar dete hain.
  if (/^https?:\/\//i.test(requestUrl)) {
    const parsedUrl = new URL(requestUrl);

    if (parsedUrl.pathname.startsWith("/api/")) {
      requestUrl =
        parsedUrl.pathname.substring(4) + parsedUrl.search;
    }
  } else if (requestUrl.startsWith("/api/")) {
    requestUrl = requestUrl.substring(4);
  } else if (requestUrl.startsWith("api/")) {
    requestUrl = "/" + requestUrl.substring(4);
  } else if (!requestUrl.startsWith("/")) {
    requestUrl = "/" + requestUrl;
  }

  const response = await api.get(requestUrl, {
    responseType: "blob",
    timeout: 30000,
  });

  const contentType =
    response.headers["content-type"] || "application/pdf";

  const blob = new Blob([response.data], {
    type: contentType,
  });

  const blobUrl = window.URL.createObjectURL(blob);

  try {
    const link = document.createElement("a");

    link.href = blobUrl;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();
  } finally {
    window.setTimeout(() => {
      window.URL.revokeObjectURL(blobUrl);
    }, 1000);
  }
}
export async function downloadProposalPdf(
  proposalId,
  proposalNumber = null
) {
  if (!proposalId) {
    throw new Error("Proposal ID is required.");
  }

  const response = await api.get(
    `/proposals/${proposalId}/pdf`,
    {
      responseType: "blob",
      timeout: 30000,
    }
  );

  const contentType =
    response.headers["content-type"] || "application/pdf";

  const pdfBlob = new Blob(
    [response.data],
    {
      type: contentType,
    }
  );

  const blobUrl = window.URL.createObjectURL(pdfBlob);

  const link = document.createElement("a");

  link.href = blobUrl;

  link.download = proposalNumber
    ? `${proposalNumber}.pdf`
    : `proposal-${proposalId}.pdf`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  // Thora delay taake browser download start kar sake.
  window.setTimeout(() => {
    window.URL.revokeObjectURL(blobUrl);
  }, 1000);
}

export default api;