import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, Navigate, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Editor } from '@tinymce/tinymce-react';

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

// Helper function for emoji fallbacks
const EmojiText = ({ children, fallback }) => {
  return (
    <span className="emoji-fallback" data-fallback={fallback}>
      {children}
    </span>
  );
};

// API helper with auth
const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  const headers = {
    ...options.headers,
  };
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  return axios({
    url: `${API}${url}`,
    ...options,
    headers
  });
};

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
          <EmojiText fallback="[HOME]">🏠</EmojiText> Sectorfive.win
        </Link>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/blog">Blog</Link>
          <Link to="/gallery">Gallery</Link>
          <Link to="/contact">Contact</Link>
          {pages && pages.filter(p => !p.is_homepage).map(page => (
            <Link key={page.id} to={`/page/${page.slug}`}>{page.title}</Link>
          ))}
          {isAuthenticated && (
            <button onClick={logout} className="nav-button">Logout</button>
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
        setContent('Welcome to Sectorfive.win! <EmojiText fallback="[ROCKET]">🚀</EmojiText>');
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
        <div className="content" dangerouslySetInnerHTML={{ __html: content }} />
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
                  <EmojiText fallback="[DATE]">📅</EmojiText> {new Date(post.created_at).toLocaleDateString()}
                </div>
                <div className="post-content" dangerouslySetInnerHTML={{ 
                  __html: post.content.length > 200 ? post.content.substring(0, 200) + '...' : post.content 
                }} />
              </div>
            ))}
          </div>
        ) : (
          <p>No blog posts yet. Check back soon! <EmojiText fallback="[NEWS]">📰</EmojiText></p>
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
  if (!post) return <div className="error">Post not found <EmojiText fallback=":(">😕</EmojiText></div>;

  return (
    <div className="page-container">
      <RetroWindow title={post.title} className="main-content">
        <div className="post-meta">
          <EmojiText fallback="[DATE]">📅</EmojiText> {new Date(post.created_at).toLocaleDateString()}
        </div>
        <div className="content" dangerouslySetInnerHTML={{ __html: post.content }} />
      </RetroWindow>
    </div>
  );
};

const Gallery = () => {
  return (
    <div className="page-container">
      <RetroWindow title="🖼️ Image Gallery" className="main-content">
        <p>Image gallery coming soon! This will showcase photos and media. <EmojiText fallback="[CAMERA]">📸</EmojiText></p>
      </RetroWindow>
    </div>
  );
};

const Contact = () => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    setError('');

    try {
      await axios.post(`${API}/contact`, formData);
      setSent(true);
      setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      console.error('Error sending message:', error);
      if (error.response?.status === 429) {
        setError(error.response.data.detail);
      } else {
        setError('Error sending message. Please try again.');
      }
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
            <EmojiText fallback="[CHECK]">✅</EmojiText> Message sent successfully! I'll get back to you soon.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="contact-form">
            {error && <div className="error-message">{error}</div>}
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
                className="retro-textarea"
              />
            </div>
            <RetroButton type="submit" disabled={sending}>
              {sending ? (
                <>
                  <EmojiText fallback="[SENDING]">📤</EmojiText> Sending...
                </>
              ) : (
                <>
                  <EmojiText fallback="[SEND]">📨</EmojiText> Send Message
                </>
              )}
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
      navigate('/management-panel');
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
            {loading ? (
              <>
                <EmojiText fallback="[LOADING]">🔄</EmojiText> Logging in...
              </>
            ) : (
              <>
                <EmojiText fallback="[LOGIN]">🚀</EmojiText> Login
              </>
            )}
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
            <EmojiText fallback="[DASH]">📊</EmojiText> Dashboard
          </button>
          <button 
            className={`tab-button ${activeTab === 'pages' ? 'active' : ''}`}
            onClick={() => setActiveTab('pages')}
          >
            <EmojiText fallback="[PAGES]">📄</EmojiText> Pages
          </button>
          <button 
            className={`tab-button ${activeTab === 'blog' ? 'active' : ''}`}
            onClick={() => setActiveTab('blog')}
          >
            <EmojiText fallback="[BLOG]">📝</EmojiText> Blog
          </button>
          <button 
            className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <EmojiText fallback="[STATS]">📈</EmojiText> Analytics
          </button>
          <button 
            className={`tab-button ${activeTab === 'contacts' ? 'active' : ''}`}
            onClick={() => setActiveTab('contacts')}
          >
            <EmojiText fallback="[MAIL]">📧</EmojiText> Contacts
          </button>
          <button 
            className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <EmojiText fallback="[SETTINGS]">⚙️</EmojiText> Settings
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'dashboard' && <AdminDashboard />}
          {activeTab === 'pages' && <AdminPages />}
          {activeTab === 'blog' && <AdminBlog />}
          {activeTab === 'analytics' && <AdminAnalytics />}
          {activeTab === 'contacts' && <AdminContacts />}
          {activeTab === 'settings' && <AdminSettings />}
        </div>
      </RetroWindow>
    </div>
  );
};

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [analytics, contacts] = await Promise.all([
          apiCall('/analytics'),
          apiCall('/contact-messages')
        ]);
        setStats({
          totalVisits: analytics.data.total_visits,
          uniqueVisitors: analytics.data.unique_visitors,
          totalContacts: contacts.data.pagination.total_results
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="admin-dashboard">
      <h3><EmojiText fallback="[TARGET]">🎯</EmojiText> Quick Stats</h3>
      <p>Welcome to your admin dashboard! Use the tabs above to manage your website.</p>
      <div className="dashboard-stats">
        <div className="stat-card">
          <h4><EmojiText fallback="[PAGES]">📄</EmojiText> Pages</h4>
          <p>Manage your website pages</p>
        </div>
        <div className="stat-card">
          <h4><EmojiText fallback="[BLOG]">📝</EmojiText> Blog</h4>
          <p>Create and manage blog posts</p>
        </div>
        <div className="stat-card">
          <h4><EmojiText fallback="[STATS]">📈</EmojiText> Analytics</h4>
          {stats ? (
            <div>
              <p>Total Visits: {stats.totalVisits}</p>
              <p>Unique Visitors: {stats.uniqueVisitors}</p>
            </div>
          ) : (
            <p>Loading stats...</p>
          )}
        </div>
        <div className="stat-card">
          <h4><EmojiText fallback="[MAIL]">📧</EmojiText> Contacts</h4>
          {stats ? (
            <p>Messages: {stats.totalContacts}</p>
          ) : (
            <p>Loading...</p>
          )}
        </div>
      </div>
    </div>
  );
};

const AdminPages = () => {
  const [pages, setPages] = useState([]);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({ title: '', slug: '', content: '' });

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const response = await apiCall('/pages');
      setPages(response.data);
    } catch (error) {
      console.error('Error fetching pages:', error);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/pages', {
        method: 'POST',
        data: formData
      });
      setCreating(false);
      setFormData({ title: '', slug: '', content: '' });
      fetchPages();
    } catch (error) {
      console.error('Error creating page:', error);
      alert('Error creating page: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      await apiCall(`/pages/${editing.id}`, {
        method: 'PUT',
        data: { title: formData.title, content: formData.content }
      });
      setEditing(null);
      setFormData({ title: '', slug: '', content: '' });
      fetchPages();
    } catch (error) {
      console.error('Error updating page:', error);
      alert('Error updating page: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (page) => {
    if (page.is_homepage) {
      alert('Cannot delete homepage');
      return;
    }
    if (window.confirm(`Delete page "${page.title}"?`)) {
      try {
        await apiCall(`/pages/${page.id}`, { method: 'DELETE' });
        fetchPages();
      } catch (error) {
        console.error('Error deleting page:', error);
        alert('Error deleting page: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const startEdit = (page) => {
    setEditing(page);
    setFormData({ title: page.title, slug: page.slug, content: page.content });
  };

  const cancelEdit = () => {
    setEditing(null);
    setCreating(false);
    setFormData({ title: '', slug: '', content: '' });
  };

  if (creating || editing) {
    return (
      <div className="admin-section">
        <h3>{creating ? 'Create New Page' : `Edit: ${editing.title}`}</h3>
        <form onSubmit={creating ? handleCreate : handleUpdate}>
          <div className="form-group">
            <label>Title:</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              className="retro-input"
            />
          </div>
          {creating && (
            <div className="form-group">
              <label>Slug (URL path):</label>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                required
                className="retro-input"
                placeholder="e.g., about-me"
              />
            </div>
          )}
          <div className="form-group">
            <label>Content:</label>
            <div className="editor-container">
              <Editor
                value={formData.content}
                onEditorChange={(content) => setFormData({ ...formData, content })}
                init={{
                  height: 400,
                  menubar: false,
                  plugins: [
                    'advlist', 'autolink', 'lists', 'link', 'image', 'charmap',
                    'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                    'insertdatetime', 'media', 'table', 'preview', 'help', 'wordcount'
                  ],
                  toolbar: 'undo redo | blocks | bold italic forecolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | help',
                  skin: 'oxide',
                  content_css: 'default'
                }}
              />
            </div>
          </div>
          <div className="admin-controls">
            <RetroButton type="submit">
              {creating ? 'Create Page' : 'Update Page'}
            </RetroButton>
            <RetroButton type="button" onClick={cancelEdit}>
              Cancel
            </RetroButton>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="admin-section">
      <div className="admin-controls">
        <h3><EmojiText fallback="[PAGES]">📄</EmojiText> Page Management</h3>
        <RetroButton onClick={() => setCreating(true)}>
          Create New Page
        </RetroButton>
      </div>
      
      <table className="admin-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Slug</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {pages.map(page => (
            <tr key={page.id}>
              <td>{page.title} {page.is_homepage && '(Homepage)'}</td>
              <td>{page.slug}</td>
              <td>{new Date(page.created_at).toLocaleDateString()}</td>
              <td>
                <RetroButton onClick={() => startEdit(page)}>Edit</RetroButton>
                {!page.is_homepage && (
                  <RetroButton onClick={() => handleDelete(page)}>Delete</RetroButton>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const AdminBlog = () => {
  const [posts, setPosts] = useState([]);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({ title: '', slug: '', content: '' });

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await axios.get(`${API}/blog`);
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/blog', {
        method: 'POST',
        data: formData
      });
      setCreating(false);
      setFormData({ title: '', slug: '', content: '' });
      fetchPosts();
    } catch (error) {
      console.error('Error creating post:', error);
      alert('Error creating post: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      await apiCall(`/blog/${editing.id}`, {
        method: 'PUT',
        data: { title: formData.title, content: formData.content }
      });
      setEditing(null);
      setFormData({ title: '', slug: '', content: '' });
      fetchPosts();
    } catch (error) {
      console.error('Error updating post:', error);
      alert('Error updating post: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (post) => {
    if (window.confirm(`Delete post "${post.title}"?`)) {
      try {
        await apiCall(`/blog/${post.id}`, { method: 'DELETE' });
        fetchPosts();
      } catch (error) {
        console.error('Error deleting post:', error);
        alert('Error deleting post: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const startEdit = (post) => {
    setEditing(post);
    setFormData({ title: post.title, slug: post.slug, content: post.content });
  };

  const cancelEdit = () => {
    setEditing(null);
    setCreating(false);
    setFormData({ title: '', slug: '', content: '' });
  };

  if (creating || editing) {
    return (
      <div className="admin-section">
        <h3>{creating ? 'Create New Blog Post' : `Edit: ${editing.title}`}</h3>
        <form onSubmit={creating ? handleCreate : handleUpdate}>
          <div className="form-group">
            <label>Title:</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              className="retro-input"
            />
          </div>
          {creating && (
            <div className="form-group">
              <label>Slug (URL path):</label>
              <input
                type="text"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                required
                className="retro-input"
                placeholder="e.g., my-first-post"
              />
            </div>
          )}
          <div className="form-group">
            <label>Content:</label>
            <div className="editor-container">
              <Editor
                value={formData.content}
                onEditorChange={(content) => setFormData({ ...formData, content })}
                init={{
                  height: 500,
                  menubar: false,
                  plugins: [
                    'advlist', 'autolink', 'lists', 'link', 'image', 'charmap',
                    'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                    'insertdatetime', 'media', 'table', 'preview', 'help', 'wordcount'
                  ],
                  toolbar: 'undo redo | blocks | bold italic forecolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | help',
                  skin: 'oxide',
                  content_css: 'default'
                }}
              />
            </div>
          </div>
          <div className="admin-controls">
            <RetroButton type="submit">
              {creating ? 'Create Post' : 'Update Post'}
            </RetroButton>
            <RetroButton type="button" onClick={cancelEdit}>
              Cancel
            </RetroButton>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="admin-section">
      <div className="admin-controls">
        <h3><EmojiText fallback="[BLOG]">📝</EmojiText> Blog Management</h3>
        <RetroButton onClick={() => setCreating(true)}>
          Create New Post
        </RetroButton>
      </div>
      
      <table className="admin-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Slug</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {posts.map(post => (
            <tr key={post.id}>
              <td>{post.title}</td>
              <td>{post.slug}</td>
              <td>{new Date(post.created_at).toLocaleDateString()}</td>
              <td>
                <RetroButton onClick={() => startEdit(post)}>Edit</RetroButton>
                <RetroButton onClick={() => handleDelete(post)}>Delete</RetroButton>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const AdminAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [search, setSearch] = useState('');
  const [country, setCountry] = useState('all');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, [search, country, page]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20'
      });
      
      if (search) params.append('search', search);
      if (country !== 'all') params.append('country', country);
      
      const response = await apiCall(`/analytics?${params}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !analytics) return <div>Loading analytics...</div>;

  return (
    <div className="admin-section">
      <h3><EmojiText fallback="[STATS]">📈</EmojiText> Website Analytics</h3>
      
      {analytics && (
        <>
          <div className="analytics-overview">
            <div className="stat-item">
              <strong>Total Visits:</strong> {analytics.total_visits}
            </div>
            <div className="stat-item">
              <strong>Unique Visitors:</strong> {analytics.unique_visitors}
            </div>
          </div>

          <div className="admin-controls">
            <input
              type="text"
              placeholder="Search IP, browser, URL..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="retro-input"
            />
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="retro-input"
            >
              <option value="all">All Countries</option>
              {analytics.top_countries.map(c => (
                <option key={c._id} value={c._id}>{c._id} ({c.count})</option>
              ))}
            </select>
          </div>

          <h4>Recent Visits</h4>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>IP Address</th>
                <th>Page</th>
                <th>Browser</th>
                <th>Country</th>
              </tr>
            </thead>
            <tbody>
              {analytics.recent_visits.map((visit, index) => (
                <tr key={index}>
                  <td>{new Date(visit.timestamp).toLocaleString()}</td>
                  <td>{visit.ip_address}</td>
                  <td>{visit.page_url}</td>
                  <td>{visit.browser}</td>
                  <td>{visit.country}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              Previous
            </button>
            <span className="current-page">
              Page {analytics.pagination.current_page} of {analytics.pagination.total_pages}
            </span>
            <button
              onClick={() => setPage(Math.min(analytics.pagination.total_pages, page + 1))}
              disabled={page === analytics.pagination.total_pages}
            >
              Next
            </button>
          </div>

          <div className="dashboard-stats">
            <div className="stat-card">
              <h4>Top Pages</h4>
              {analytics.top_pages.map(page => (
                <div key={page._id}>
                  {page._id}: {page.count} visits
                </div>
              ))}
            </div>
            <div className="stat-card">
              <h4>Top Browsers</h4>
              {analytics.top_browsers.map(browser => (
                <div key={browser._id}>
                  {browser._id}: {browser.count} visits
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const AdminContacts = () => {
  const [contacts, setContacts] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchContacts();
  }, [search, page]);

  const fetchContacts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10'
      });
      
      if (search) params.append('search', search);
      
      const response = await apiCall(`/contact-messages?${params}`);
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (messageId) => {
    if (window.confirm('Delete this message?')) {
      try {
        await apiCall(`/contact-messages/${messageId}`, { method: 'DELETE' });
        fetchContacts();
      } catch (error) {
        console.error('Error deleting message:', error);
        alert('Error deleting message');
      }
    }
  };

  if (loading && !contacts) return <div>Loading contacts...</div>;

  return (
    <div className="admin-section">
      <h3><EmojiText fallback="[MAIL]">📧</EmojiText> Contact Messages</h3>
      
      {contacts && (
        <>
          <div className="admin-controls">
            <input
              type="text"
              placeholder="Search name, email, message..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="retro-input"
            />
          </div>

          <table className="admin-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Name</th>
                <th>Email</th>
                <th>Message</th>
                <th>IP</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {contacts.messages.map((message) => (
                <tr key={message.id}>
                  <td>{new Date(message.created_at).toLocaleString()}</td>
                  <td>{message.name}</td>
                  <td>{message.email}</td>
                  <td>{message.message.substring(0, 100)}...</td>
                  <td>{message.ip_address}</td>
                  <td>
                    <RetroButton onClick={() => handleDelete(message.id)}>
                      Delete
                    </RetroButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              Previous
            </button>
            <span className="current-page">
              Page {contacts.pagination.current_page} of {contacts.pagination.total_pages}
            </span>
            <button
              onClick={() => setPage(Math.min(contacts.pagination.total_pages, page + 1))}
              disabled={page === contacts.pagination.total_pages}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

const AdminSettings = () => {
  const [settings, setSettings] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await apiCall('/settings');
      setSettings(response.data);
      setFormData(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const formDataObj = new FormData();
      Object.keys(formData).forEach(key => {
        formDataObj.append(key, formData[key]);
      });
      
      await apiCall('/settings', {
        method: 'PUT',
        data: formDataObj
      });
      alert('Settings updated successfully!');
    } catch (error) {
      console.error('Error updating settings:', error);
      alert('Error updating settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading settings...</div>;

  return (
    <div className="admin-section">
      <h3><EmojiText fallback="[SETTINGS]">⚙️</EmojiText> Website Settings</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Site Title:</label>
          <input
            type="text"
            value={formData.site_title || ''}
            onChange={(e) => setFormData({ ...formData, site_title: e.target.value })}
            className="retro-input"
          />
        </div>
        
        <div className="form-group">
          <label>Site Email:</label>
          <input
            type="email"
            value={formData.site_email || ''}
            onChange={(e) => setFormData({ ...formData, site_email: e.target.value })}
            className="retro-input"
          />
        </div>
        
        <div className="form-group">
          <label>Max File Size (bytes):</label>
          <input
            type="number"
            value={formData.max_file_size || 5368709120}
            onChange={(e) => setFormData({ ...formData, max_file_size: parseInt(e.target.value) })}
            className="retro-input"
          />
          <small>Current: {Math.round((formData.max_file_size || 0) / 1024 / 1024 / 1024)} GB</small>
        </div>
        
        <div className="form-group">
          <label>Contact Form Cooldown (seconds):</label>
          <input
            type="number"
            value={formData.contact_cooldown || 300}
            onChange={(e) => setFormData({ ...formData, contact_cooldown: parseInt(e.target.value) })}
            className="retro-input"
          />
          <small>Current: {Math.round((formData.contact_cooldown || 0) / 60)} minutes</small>
        </div>
        
        <RetroButton type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </RetroButton>
      </form>
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
  if (!page) return <div className="error">Page not found <EmojiText fallback=":(">😕</EmojiText></div>;

  return (
    <div className="page-container">
      <RetroWindow title={page.title} className="main-content">
        <div className="content" dangerouslySetInnerHTML={{ __html: page.content }} />
      </RetroWindow>
    </div>
  );
};

function App() {
  const [pages, setPages] = useState([]);

  useEffect(() => {
    // Note: We can't fetch pages for navigation without auth, so we'll skip this for now
    // In production, you might want a public endpoint for navigation pages only
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
              <Route path="/management-panel" element={<Admin />} />
              <Route path="/page/:slug" element={<PageView />} />
            </Routes>
          </main>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;