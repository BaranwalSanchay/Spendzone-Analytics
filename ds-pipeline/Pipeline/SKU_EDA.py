import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import os  # Added for directory management
# Import plotly io for saving as PNG
import plotly.io as pio

# Set matplotlib to non-blocking interactive mode
plt.ion()

class ProductAnalytics:
    def __init__(self, data):
        self.data = data

    def plot_sunburst(self, save=False, save_dir=None, display=True):
        """Creates a Sunburst chart showing the hierarchy of categories, subcategories, and products."""
        fig = px.sunburst(self.data, 
                          path=["product_analytic_category", "product_analytic_sub_category", "product_analytic_vertical"], 
                          title="Product Hierarchy")
        if display:
            fig.show()
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            # Save as PNG instead of HTML
            fig.write_image(os.path.join(save_dir, "sunburst_chart.png"), width=1200, height=800)

    def plot_histograms(self, save=False, save_dir=None, display=True):
        """Creates histograms for product categories and subcategories."""
        fig_hist_pac = px.histogram(self.data, x="product_analytic_category", 
                                    title="Histogram of Product Categories", 
                                    text_auto=True, color_discrete_sequence=['blue'])
        fig_hist_pac.update_layout(xaxis_title="Product Analytic Category", yaxis_title="Count", bargap=0.2)
        if display:
            fig_hist_pac.show()
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            # Save as PNG instead of HTML
            fig_hist_pac.write_image(os.path.join(save_dir, "histogram_categories.png"), width=1200, height=800)

        fig_hist_pasc = px.histogram(self.data, x="product_analytic_sub_category", 
                                     title="Histogram of Product Subcategories", 
                                     text_auto=True, color_discrete_sequence=['Green'])
        fig_hist_pasc.update_layout(xaxis_title="Product Analytic Sub Category", yaxis_title="Count", bargap=0.2)
        if display:
            fig_hist_pasc.show()
        
        if save and save_dir:
            # Save as PNG instead of HTML
            fig_hist_pasc.write_image(os.path.join(save_dir, "histogram_subcategories.png"), width=1200, height=800)

    def plot_pie_chart(self, save=False, save_dir=None, display=True):
        """Creates a Pie chart for product category distribution."""
        category_counts_pac = self.data["product_analytic_category"].value_counts().reset_index()
        category_counts_pac.columns = ["product_analytic_category", "count"]

        fig_pie_pac = px.pie(category_counts_pac, names="product_analytic_category", 
                             values="count", title="Pie Chart of Product Categories",
                             hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)

        fig_pie_pac.update_traces(textinfo='percent+label', pull=[0.1, 0, 0])  # Highlight first slice
        if display:
            fig_pie_pac.show()
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            # Save as PNG instead of HTML
            fig_pie_pac.write_image(os.path.join(save_dir, "pie_chart_categories.png"), width=1200, height=800)

    def plot_top_products_bar_chart(self, top_n=10, save=False, save_dir=None, display=True):
        """Creates a bar chart of the top N most frequent products."""
        top_products = self.data["product_analytic_vertical"].value_counts().head(top_n).reset_index()
        top_products.columns = ["product", "count"]

        fig = px.bar(top_products, x="product", y="count", text="count",
                     title=f"Top {top_n} Most Frequent Products",
                     labels={"product": "Product Name", "count": "Frequency"},
                     color="count", color_continuous_scale="Blues")

        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(width=1000, height=700, font=dict(size=14))
        if display:
            fig.show()
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            # Save as PNG instead of HTML
            fig.write_image(os.path.join(save_dir, "top_products_bar_chart.png"), width=1200, height=800)

    def plot_category_subcategory_heatmap(self, save=False, save_dir=None, display=True):
        """Creates a heatmap showing the relationship between categories and subcategories."""
        category_subcategory_counts = pd.crosstab(self.data["product_analytic_category"], self.data["product_analytic_sub_category"])

        # Option 1: Use Plotly instead of matplotlib for consistency
        fig = px.imshow(category_subcategory_counts, 
                       labels=dict(x="Subcategory", y="Category", color="Count"),
                       title="Heatmap of Subcategories under Each Category")
        fig.update_layout(width=1200, height=800)
        if display:
            fig.show()
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            fig.write_image(os.path.join(save_dir, "category_subcategory_heatmap.png"), width=1200, height=800)
        
        # Option 2: If you still want to use matplotlib but non-blocking
        # Comment out the above and uncomment this if you prefer matplotlib's heatmap
        """
        plt.figure(figsize=(12, 6))
        sns.heatmap(category_subcategory_counts, cmap="coolwarm", annot=True, fmt="d")
        plt.title("Heatmap of Subcategories under Each Category")
        plt.xticks(rotation=90)
        plt.yticks(rotation=0)
        # Use plt.draw() and plt.pause() instead of plt.show() for non-blocking behavior
        plt.draw()
        plt.pause(0.001)  # Small pause to render the plot
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, "category_subcategory_heatmap.png"), bbox_inches="tight")
        """

    def plot_wordcloud(self, save=False, save_dir=None, display=True):
        """Creates a Word Cloud for the most common product names."""
        text = " ".join(self.data["product_analytic_vertical"].dropna())

        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

        # Use plotly for wordcloud (consistent with other plots)
        # Create a plotly figure with the wordcloud image
        fig = go.Figure()
        
        # Convert wordcloud to image
        wordcloud_img = wordcloud.to_array()
        
        # Add image to figure
        fig.add_trace(go.Image(z=wordcloud_img))
        fig.update_layout(title="Most Common Words in Product Names",
                         width=1000, height=600)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        
        if display:
            fig.show()
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            fig.write_image(os.path.join(save_dir, "product_names_wordcloud.png"), width=1200, height=800)
        
        # Option 2: If you still want to use matplotlib but non-blocking
        # Comment out the above and uncomment this if you prefer matplotlib's wordcloud
        """
        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title("Most Common Words in Product Names")
        # Use plt.draw() and plt.pause() instead of plt.show() for non-blocking behavior
        plt.draw()
        plt.pause(0.001)  # Small pause to render the plot
        
        if save and save_dir:
            os.makedirs(save_dir, exist_ok=True)
            plt.savefig(os.path.join(save_dir, "product_names_wordcloud.png"), bbox_inches="tight")
        """

    def save_all_plots(self, save_dir="Graphs_SKU"):
        """Saves all charts and visualizations to the specified directory."""
        os.makedirs(save_dir, exist_ok=True)
        print(f"Saving all plots to '{save_dir}' directory...")
        
        print("Saving Sunburst Chart...")
        self.plot_sunburst(save=True, save_dir=save_dir, display=False)
        
        print("Saving Histograms...")
        self.plot_histograms(save=True, save_dir=save_dir, display=False)
        
        print("Saving Pie Chart...")
        self.plot_pie_chart(save=True, save_dir=save_dir, display=False)
        
        print("Saving Top Products Bar Chart...")
        self.plot_top_products_bar_chart(save=True, save_dir=save_dir, display=False)
        
        print("Saving Heatmap...")
        self.plot_category_subcategory_heatmap(save=True, save_dir=save_dir, display=False)
        
        print("Saving Word Cloud...")
        self.plot_wordcloud(save=True, save_dir=save_dir, display=False)
        
        print(f"All plots have been saved to '{save_dir}'")

    def generate_all_plots(self):
        """Generates all charts and visualizations."""
        print("Generating Sunburst Chart...")
        self.plot_sunburst()

        print("Generating Histograms...")
        self.plot_histograms()

        print("Generating Pie Chart...")
        self.plot_pie_chart()

        print("Generating Top Products Bar Chart...")
        self.plot_top_products_bar_chart()

        print("Generating Heatmap...")
        self.plot_category_subcategory_heatmap()

        print("Generating Word Cloud...")
        self.plot_wordcloud()

def main():
    dataset_path = input("Enter the path to your dataset (CSV file): ")  # Get dataset path from user
    try:
        df = pd.read_csv(dataset_path)  # Load dataset
        analytics = ProductAnalytics(df)  # Create an instance
        
        # Always generate and display plots
        print("Generating and displaying plots...")
        analytics.generate_all_plots()  # Run all visualizations
        
        # Always save plots
        print("Saving all plots to 'Graphs_SKU' folder...")
        analytics.save_all_plots()  # Save all visualizations
            
    except FileNotFoundError:
        print(f"Error: The file '{dataset_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

