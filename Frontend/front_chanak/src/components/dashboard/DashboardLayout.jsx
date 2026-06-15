import { Outlet } from 'react-router-dom'
import '../../styles/dashboard.css'

function DashboardLayout() {
  return (
    <div className="dashboard-container">
      <Outlet />
    </div>
  )
}

export default DashboardLayout

