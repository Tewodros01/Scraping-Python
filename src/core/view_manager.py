class ViewManager:
    def __init__(self, root):
        self.root = root
        self.views = {}

        # Configure the root window to expand and fill
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def add_view(self, name, view_class):
        """Add a view to the manager"""
        frame = view_class(self.root, self)
        self.views[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def show_view(self, name):
        """Show a specific view"""
        frame = self.views[name]
        frame.tkraise()

    def show_job_listings(self, site_name, jobs):
        """Show the job listings view for the selected site"""
        job_listings_view = self.views.get("JobListingsView")
        if job_listings_view:
            job_listings_view.display_jobs(site_name, jobs)
            self.show_view("JobListingsView")

    def update_unposted_jobs(self, unposted_jobs):
        """Update the UnpostedJobsView with the list of unposted jobs"""
        unposted_jobs_view = self.views.get("UnpostedJobsView")
        if unposted_jobs_view:
            unposted_jobs_view.update_unposted_jobs(unposted_jobs)

    def show_unposted_jobs_view(self, unposted_jobs):
        """Show the UnpostedJobsView with the unposted jobs"""
        self.update_unposted_jobs(unposted_jobs)
        self.show_view("UnpostedJobsView")
