import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, Navigate, useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const login = (token) => {
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// Components
const RetroButton = ({ children, onClick, className = "", type = "button", disabled = false }) => (
  <button
    type={type}
    onClick={onClick}
    disabled={disabled}
    className={`retro-button ${className} ${disabled ? 'disabled' : ''}`}
  >
    {children}
  </button>
);

const RetroWindow = ({ title, children, className = "" }) => (
  <div className={`retro-window ${className}`}>
    <div className="window-header">
      <div className="window-title">{title}</div>
    </div>
    <div className="window-content">
      {children}
    </div>
  </div>
);

const Navigation = ({ pages }) => {
  const { isAuthenticated, logout } = useAuth();
  
  return (
    <nav className="retro-nav">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          🏠 Sectorfive.win
        </Link>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/blog">Blog</Link>
          <Link to="/gallery">Gallery</Link>
          <Link to="/contact">Contact</Link>
          {pages && pages.filter(p => !p.is_homepage).map(page => (
            <Link key={page.id} to={`/page/${page.slug}`}>{page.title}</Link>
          ))}
          {isAuthenticated ? (
            <>
              <Link to="/admin">Admin</Link>
              <button onClick={logout} className="nav-button">Logout</button>
            </>
          ) : (
            <Link to="/login">Admin Login</Link>
          )}
        </div>
      </div>
    </nav>
  );
};

const Home = () => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHomepage = async () => {
      try {
        const response = await axios.get(`${API}/page/home`);
        setContent(response.data.content);
      } catch (error) {
        console.error('Error fetching homepage:', error);
        setContent('Welcome to Sectorfive.win! 🚀');
      } finally {
        setLoading(false);
      }
    };

    fetchHomepage();
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="retro-spinner"></div>
        Loading...
      </div>
    );
  }

  return (
    <div className="page-container">
      <RetroWindow title="🏠 Welcome to Sectorfive.win" className="main-content">
        <div className="content" dangerouslySetInnerHTML={{ __html: content.replace(/\n/g, '<br/>') }} />
      </RetroWindow>
    </div>
  );
};

const Blog = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await axios.get(`${API}/blog`);
        setPosts(response.data);
      } catch (error) {
        console.error('Error fetching blog posts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  if (loading) {
    return <div className="loading">Loading blog posts...</div>;
  }

  return (
    <div className="page-container">
      <RetroWindow title="📝 Blog Posts" className="main-content">
        {posts.length > 0 ? (
          <div className="blog-posts">
            {posts.map(post => (
              <div key={post.id} className="blog-post-preview">
                <h3>
                  <Link to={`/blog/${post.slug}`}>{post.title}</Link>
                </h3>
                <div className="post-meta">
                  {new Date(post.created_at).toLocaleDateString()}
                </div>
                <div className="post-content">
                  {post.content.substring(0, 200)}...
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No blog posts yet. Check back soon! 📰</p>
        )}
      </RetroWindow>
    </div>
  );
};

const BlogPost = () => {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const response = await axios.get(`${API}/blog/${slug}`);
        setPost(response.data);
      } catch (error) {
        console.error('Error fetching blog post:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [slug]);

  if (loading) return <div className="loading">Loading post...</div>;
  if (!post) return <div className="error">Post not found 😕</div>;

  return (
    <div className="page-container">
      <RetroWindow title={post.title} className="main-content">
        <div className="post-meta">
          📅 {new Date(post.created_at).toLocaleDateString()}
        </div>
        <div className="content" dangerouslySetInnerHTML={{ __html: post.content.replace(/\n/g, '<br/>') }} />
      </RetroWindow>
    </div>
  );
};

const Gallery = () => {
  return (
    <div className="page-container">
      <RetroWindow title="🖼️ Image Gallery" className="main-content">
        <p>Image gallery coming soon! This will showcase photos and media. 📸</p>
      </RetroWindow>
    </div>
  );
};

const Contact = () => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);

    try {
      const formDataObj = new FormData();
      formDataObj.append('name', formData.name);
      formDataObj.append('email', formData.email);
      formDataObj.append('message', formData.message);

      await axios.post(`${API}/contact`, formDataObj);
      setSent(true);
      setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Error sending message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="page-container">
      <RetroWindow title="📬 Contact Me" className="main-content">
        {sent ? (
          <div className="success-message">
            ✅ Message sent successfully! I'll get back to you soon.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="contact-form">
            <div className="form-group">
              <label>Name:</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="retro-input"
              />
            </div>
            <div className="form-group">
              <label>Email:</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="retro-input"
              />
            </div>
            <div className="form-group">
              <label>Message:</label>
              <textarea
                name="message"
                value={formData.message}
                onChange={handleChange}
                required
                rows="5"
                className="retro-input"
              />
            </div>
            <RetroButton type="submit" disabled={sending}>
              {sending ? '📤 Sending...' : '📨 Send Message'}
            </RetroButton>
          </form>
        )}
      </RetroWindow>
    </div>
  );
};

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/login`, credentials);
      login(response.data.access_token);
      navigate('/admin');
    } catch (error) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setCredentials({ ...credentials, [e.target.name]: e.target.value });
  };

  return (
    <div className="page-container">
      <RetroWindow title="🔐 Admin Login" className="login-window">
        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="error-message">{error}</div>}
          <div className="form-group">
            <label>Username:</label>
            <input
              type="text"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              required
              className="retro-input"
            />
          </div>
          <div className="form-group">
            <label>Password:</label>
            <input
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
              className="retro-input"
            />
          </div>
          <RetroButton type="submit" disabled={loading}>
            {loading ? '🔄 Logging in...' : '🚀 Login'}
          </RetroButton>
        </form>
      </RetroWindow>
    </div>
  );
};

const Admin = () => {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="page-container">
      <RetroWindow title="⚙️ Admin Dashboard" className="admin-window">
        <div className="admin-tabs">
          <button 
            className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={`tab-button ${activeTab === 'pages' ? 'active' : ''}`}
            onClick={() => setActiveTab('pages')}
          >
            📄 Pages
          </button>
          <button 
            className={`tab-button ${activeTab === 'blog' ? 'active' : ''}`}
            onClick={() => setActiveTab('blog')}
          >
            📝 Blog
          </button>
          <button 
            className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            📈 Analytics
          </button>
          <button 
            className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ Settings
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'dashboard' && <AdminDashboard />}
          {activeTab === 'pages' && <AdminPages />}
          {activeTab === 'blog' && <AdminBlog />}
          {activeTab === 'analytics' && <AdminAnalytics />}
          {activeTab === 'settings' && <AdminSettings />}
        </div>
      </RetroWindow>
    </div>
  );
};

const AdminDashboard = () => {
  return (
    <div className="admin-dashboard">
      <h3>🎯 Quick Stats</h3>
      <p>Welcome to your admin dashboard! Use the tabs above to manage your website.</p>
      <div className="dashboard-stats">
        <div className="stat-card">
          <h4>📄 Pages</h4>
          <p>Manage your website pages</p>
        </div>
        <div className="stat-card">
          <h4>📝 Blog</h4>
          <p>Create and manage blog posts</p>
        </div>
        <div className="stat-card">
          <h4>📈 Analytics</h4>
          <p>View visitor statistics</p>
        </div>
      </div>
    </div>
  );
};

const AdminPages = () => {
  return (
    <div className="admin-section">
      <h3>📄 Page Management</h3>
      <p>Page management features coming soon!</p>
    </div>
  );
};

const AdminBlog = () => {
  return (
    <div className="admin-section">
      <h3>📝 Blog Management</h3>
      <p>Blog management features coming soon!</p>
    </div>
  );
};

const AdminAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API}/analytics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAnalytics(response.data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) return <div>Loading analytics...</div>;

  return (
    <div className="admin-section">
      <h3>📈 Website Analytics</h3>
      {analytics && (
        <div className="analytics-overview">
          <div className="stat-item">
            <strong>Total Visits:</strong> {analytics.total_visits}
          </div>
          <div className="stat-item">
            <strong>Unique Visitors:</strong> {analytics.unique_visitors}
          </div>
        </div>
      )}
    </div>
  );
};

const AdminSettings = () => {
  return (
    <div className="admin-section">
      <h3>⚙️ Settings</h3>
      <p>Settings management coming soon!</p>
    </div>
  );
};

const PageView = () => {
  const { slug } = useParams();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPage = async () => {
      try {
        const response = await axios.get(`${API}/page/${slug}`);
        setPage(response.data);
      } catch (error) {
        console.error('Error fetching page:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPage();
  }, [slug]);

  if (loading) return <div className="loading">Loading page...</div>;
  if (!page) return <div className="error">Page not found 😕</div>;

  return (
    <div className="page-container">
      <RetroWindow title={page.title} className="main-content">
        <div className="content" dangerouslySetInnerHTML={{ __html: page.content.replace(/\n/g, '<br/>') }} />
      </RetroWindow>
    </div>
  );
};

function App() {
  const [pages, setPages] = useState([]);

  useEffect(() => {
    // Fetch pages for navigation (public endpoint)
    const fetchPages = async () => {
      try {
        const response = await axios.get(`${API}/pages`);
        setPages(response.data);
      } catch (error) {
        console.error('Error fetching pages:', error);
      }
    };

    fetchPages();
  }, []);

  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Navigation pages={pages} />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/blog/:slug" element={<BlogPost />} />
              <Route path="/gallery" element={<Gallery />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/login" element={<Login />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/page/:slug" element={<PageView />} />
            </Routes>
          </main>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;