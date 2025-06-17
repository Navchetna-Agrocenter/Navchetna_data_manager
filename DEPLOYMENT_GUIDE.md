# 🚀 Deployment Guide: Streamlit Cloud + MongoDB

This guide will help you deploy the Navchetna Plantation Management System to Streamlit Cloud with MongoDB Atlas.

## 📋 Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **MongoDB Atlas Account**: Free tier is sufficient for testing
3. **Streamlit Cloud Account**: Free account at [share.streamlit.io](https://share.streamlit.io)

## 🗄️ Step 1: Set Up MongoDB Atlas

### 1.1 Create MongoDB Atlas Cluster
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Sign up for a free account
3. Create a new cluster (M0 Sandbox - Free tier)
4. Choose a cloud provider and region
5. Wait for cluster to be created (2-3 minutes)

### 1.2 Configure Database Access
1. In Atlas dashboard, go to **Database Access**
2. Click **Add New Database User**
3. Create a user with username/password authentication
4. Set privileges to **Read and write to any database**
5. Note down the **username** and **password**

### 1.3 Configure Network Access
1. Go to **Network Access**
2. Click **Add IP Address**
3. Select **Allow Access from Anywhere** (0.0.0.0/0)
4. This is needed for Streamlit Cloud to connect

### 1.4 Get Connection String
1. Go to **Clusters** and click **Connect**
2. Choose **Connect your application**
3. Select **Python** and version **3.6 or later**
4. Copy the connection string
5. Replace `<password>` with your actual password
6. Replace `<dbname>` with `navchetna_data`

Example connection string:
```
mongodb+srv://username:password@cluster0.abc123.mongodb.net/navchetna_data?retryWrites=true&w=majority
```

## 🌐 Step 2: Deploy to Streamlit Cloud

### 2.1 Prepare Repository
1. Ensure your repository has these files:
   - `main_mongodb.py` (main application)
   - `requirements.txt` (dependencies)
   - `.streamlit/config.toml` (configuration)
   - `utils/` folder with all utility files

### 2.2 Deploy Application
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository
5. Set **Main file path** to: `main_mongodb.py`
6. Click **Deploy**

### 2.3 Configure Secrets
1. In your Streamlit Cloud app dashboard, go to **Settings**
2. Click on **Secrets**
3. Add the following secrets:

```toml
[mongodb]
connection_string = "mongodb+srv://username:password@cluster0.abc123.mongodb.net/navchetna_data?retryWrites=true&w=majority"
database_name = "navchetna_data"

[app]
admin_password = "your-secure-admin-password"
secret_key = "your-secret-key-for-sessions"
```

**Important**: Replace with your actual MongoDB connection string and secure passwords.

## 🔧 Step 3: Verify Deployment

### 3.1 Check Application Status
1. Wait for deployment to complete (2-5 minutes)
2. Check the logs for any errors
3. Ensure the app shows "Connected to MongoDB successfully"

### 3.2 Test Functionality
1. **Login**: Use `admin` / `admin` for first login
2. **Create Projects**: Test project creation
3. **Add Data**: Test data entry functionality
4. **Generate Reports**: Test all report types including PDF downloads
5. **Dashboard**: Verify charts and visualizations load correctly

### 3.3 Initial Setup
1. **Change Admin Password**: Go to User Management and update admin password
2. **Create Projects**: Set up your actual projects
3. **Add Users**: Create additional users as needed
4. **Configure Schema**: Set up custom fields if required

## 🛠️ Step 4: Troubleshooting

### Common Issues and Solutions

#### 4.1 MongoDB Connection Issues
**Error**: "MongoDB connection error"

**Solutions**:
- Verify connection string is correct in secrets
- Check MongoDB Atlas network access allows 0.0.0.0/0
- Ensure database user has proper permissions
- Check if cluster is active and running

#### 4.2 Missing Dependencies
**Error**: "ModuleNotFoundError"

**Solutions**:
- Check `requirements.txt` has all required packages
- Ensure package versions are compatible
- Redeploy the application

#### 4.3 PDF Generation Issues
**Error**: PDF downloads not working

**Solutions**:
- Verify `reportlab` and `fpdf2` are in requirements.txt
- Check application logs for PDF generation errors
- Test with smaller datasets first

#### 4.4 Data Not Persisting
**Error**: Data disappears after restart

**Solutions**:
- Verify MongoDB connection is working
- Check that data is being written to MongoDB (not just local files)
- Monitor MongoDB Atlas for data insertion

## 📊 Step 5: Production Considerations

### 5.1 Security
- [ ] Change default admin password
- [ ] Use strong, unique passwords for all users
- [ ] Enable MongoDB Atlas IP whitelisting for production
- [ ] Use environment-specific secrets

### 5.2 Performance
- [ ] Monitor MongoDB Atlas usage
- [ ] Optimize queries for large datasets
- [ ] Consider MongoDB Atlas auto-scaling
- [ ] Monitor Streamlit Cloud resource usage

### 5.3 Backup
- [ ] Enable MongoDB Atlas automated backups
- [ ] Export critical data regularly
- [ ] Document data schema and configurations
- [ ] Keep local backups of important configurations

### 5.4 Monitoring
- [ ] Set up MongoDB Atlas alerts
- [ ] Monitor application performance in Streamlit Cloud
- [ ] Track user activity and system usage
- [ ] Set up error notifications

## 🔄 Step 6: Updates and Maintenance

### 6.1 Application Updates
1. Make changes in your GitHub repository
2. Streamlit Cloud will auto-deploy on push to main branch
3. Monitor deployment logs for issues
4. Test functionality after updates

### 6.2 Database Maintenance
1. Monitor MongoDB Atlas storage usage
2. Review and optimize collections periodically
3. Clean up old/unused data
4. Update indexes for better performance

### 6.3 User Management
1. Regularly review user access
2. Remove inactive users
3. Update user permissions as needed
4. Monitor user activity logs

## 📞 Support

### Getting Help
- **Streamlit Cloud**: [Streamlit Community Forum](https://discuss.streamlit.io/)
- **MongoDB Atlas**: [MongoDB Documentation](https://docs.atlas.mongodb.com/)
- **Application Issues**: Check GitHub repository issues

### Key Resources
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-cloud)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)

---

## ✅ Deployment Checklist

Before going live:

- [ ] MongoDB Atlas cluster created and configured
- [ ] Database user created with proper permissions
- [ ] Network access configured for Streamlit Cloud
- [ ] Connection string tested and working
- [ ] Streamlit Cloud app deployed successfully
- [ ] Secrets configured correctly
- [ ] Admin password changed from default
- [ ] Test projects and users created
- [ ] All functionality tested (CRUD operations, reports, dashboard)
- [ ] PDF downloads working
- [ ] Performance acceptable for expected user load
- [ ] Backup strategy in place

**🎉 Your plantation management system is now live and ready for production use!** 