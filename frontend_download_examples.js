/**
 * Frontend JavaScript examples for downloading documents from POCA service
 */

// Method 1: Simple download function
async function downloadDocument(downloadLink, filename, token) {
    try {
        const response = await fetch(downloadLink, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            console.log('✓ Document downloaded successfully');
        } else {
            console.error('✗ Download failed:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('✗ Download error:', error);
    }
}

// Method 2: Download with progress tracking
async function downloadDocumentWithProgress(downloadLink, filename, token, progressCallback) {
    try {
        const response = await fetch(downloadLink, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentLength = response.headers.get('content-length');
        const total = parseInt(contentLength, 10);
        let loaded = 0;
        
        const reader = response.body.getReader();
        const chunks = [];
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            chunks.push(value);
            loaded += value.length;
            
            if (progressCallback && total) {
                progressCallback(loaded, total);
            }
        }
        
        const blob = new Blob(chunks);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        console.log('✓ Document downloaded successfully');
    } catch (error) {
        console.error('✗ Download error:', error);
    }
}

// Method 3: React component example
function DocumentDownloadButton({ document, token }) {
    const [downloading, setDownloading] = useState(false);
    
    const handleDownload = async () => {
        setDownloading(true);
        try {
            await downloadDocument(
                document.download_link, 
                document.file_name, 
                token
            );
        } finally {
            setDownloading(false);
        }
    };
    
    return (
        <button 
            onClick={handleDownload} 
            disabled={downloading}
            className="download-btn"
        >
            {downloading ? 'Downloading...' : 'Download'}
        </button>
    );
}

// Method 4: Vue.js component example
const DocumentDownload = {
    props: ['document', 'token'],
    data() {
        return {
            downloading: false
        };
    },
    methods: {
        async handleDownload() {
            this.downloading = true;
            try {
                await downloadDocument(
                    this.document.download_link,
                    this.document.file_name,
                    this.token
                );
            } finally {
                this.downloading = false;
            }
        }
    },
    template: `
        <button 
            @click="handleDownload" 
            :disabled="downloading"
            class="download-btn"
        >
            {{ downloading ? 'Downloading...' : 'Download' }}
        </button>
    `
};

// Method 5: Angular service example
class DocumentDownloadService {
    constructor(private http: HttpClient) {}
    
    async downloadDocument(downloadLink: string, filename: string, token: string): Promise<void> {
        const headers = new HttpHeaders({
            'Authorization': `Bearer ${token}`
        });
        
        try {
            const response = await this.http.get(downloadLink, {
                headers,
                responseType: 'blob'
            }).toPromise();
            
            const blob = new Blob([response]);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            console.log('✓ Document downloaded successfully');
        } catch (error) {
            console.error('✗ Download error:', error);
        }
    }
}

// Method 6: jQuery example
function downloadDocumentJQuery(downloadLink, filename, token) {
    $.ajax({
        url: downloadLink,
        type: 'GET',
        headers: {
            'Authorization': 'Bearer ' + token
        },
        xhrFields: {
            responseType: 'blob'
        },
        success: function(data) {
            const blob = new Blob([data]);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            console.log('✓ Document downloaded successfully');
        },
        error: function(xhr, status, error) {
            console.error('✗ Download failed:', status, error);
        }
    });
}

// Usage examples:

// Example 1: Simple usage
const token = localStorage.getItem('access_token');
const downloadLink = 'http://localhost:8000/api/v1/documents/123/download';
const filename = 'document.pdf';
downloadDocument(downloadLink, filename, token);

// Example 2: With progress tracking
downloadDocumentWithProgress(downloadLink, filename, token, (loaded, total) => {
    const progress = (loaded / total) * 100;
    console.log(`Download progress: ${progress.toFixed(2)}%`);
});

// Example 3: Download all patient documents
async function downloadAllPatientDocuments(patientId, token) {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/patients/${patientId}/documents`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            const documents = result.data.documents;
            
            for (const doc of documents) {
                await downloadDocument(doc.download_link, doc.file_name, token);
                // Add delay between downloads to avoid overwhelming the server
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
    } catch (error) {
        console.error('Error downloading patient documents:', error);
    }
}
