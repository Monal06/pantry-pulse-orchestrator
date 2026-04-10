import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Button, TextField, Chip,
  Snackbar, Alert, Tabs, Tab, Stack, Dialog, DialogTitle,
  DialogContent, DialogActions, Fab, LinearProgress,
} from "@mui/material";
import { Add } from "@mui/icons-material";
import { getCommunityListings, getMyListings, createCommunityListing, claimListing } from "../api";

export default function CommunityPage() {
  const [tab, setTab] = useState(0);
  const [listings, setListings] = useState<any[]>([]);
  const [myListings, setMyListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const [itemName, setItemName] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [community, mine] = await Promise.all([getCommunityListings(), getMyListings()]);
      setListings(community);
      setMyListings(mine);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handlePost = async () => {
    if (!itemName.trim()) return;
    try {
      await createCommunityListing({
        item_name: itemName.trim(),
        category: "other",
        quantity: parseFloat(quantity) || 1,
        unit: "item",
        description: description.trim(),
        pickup_location: location.trim(),
        hours_available: 24,
      });
      setDialogOpen(false);
      setItemName("");
      setQuantity("1");
      setDescription("");
      setLocation("");
      setSnackbar("Posted! Your neighbors can now claim this.");
      await loadData();
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const handleClaim = async (id: string) => {
    try {
      await claimListing(id);
      setSnackbar("Claimed! Contact the poster to arrange pickup.");
      await loadData();
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const displayList = tab === 0 ? listings : myListings;

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Community Sharing</Typography>
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={`Available (${listings.length})`} />
        <Tab label={`My Posts (${myListings.length})`} />
      </Tabs>

      {displayList.length === 0 && (
        <Box sx={{ textAlign: "center", py: 6 }}>
          <Typography color="text.secondary">
            {tab === 0
              ? "No surplus food available right now. Check back later!"
              : "You haven't posted any surplus food yet."}
          </Typography>
        </Box>
      )}

      {displayList.map((listing: any) => (
        <Card key={listing.id} sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="h6" fontWeight={700}>{listing.item_name}</Typography>
              <Chip label={`${listing.quantity} ${listing.unit}`} size="small" />
            </Stack>
            {listing.description && (
              <Typography color="text.secondary" sx={{ mb: 0.5 }}>{listing.description}</Typography>
            )}
            {listing.pickup_location && (
              <Typography variant="body2" sx={{ color: "#1565C0", mb: 1 }}>
                Pickup: {listing.pickup_location}
              </Typography>
            )}
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip label={listing.status} size="small" sx={{ bgcolor: "#E8F5E9" }} />
              <Typography variant="caption" color="text.secondary">
                Expires: {new Date(listing.expires_at).toLocaleString()}
              </Typography>
            </Stack>
            {tab === 0 && listing.status === "available" && (
              <Button variant="contained" onClick={() => handleClaim(listing.id)} sx={{ mt: 1.5 }}>
                Claim This
              </Button>
            )}
          </CardContent>
        </Card>
      ))}

      <Fab
        color="primary"
        onClick={() => setDialogOpen(true)}
        sx={{ position: "fixed", bottom: 24, right: 24 }}
      >
        <Add />
      </Fab>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Share Surplus Food</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Food item *" value={itemName} onChange={(e) => setItemName(e.target.value)} fullWidth />
            <TextField label="Quantity" value={quantity} onChange={(e) => setQuantity(e.target.value)} type="number" fullWidth />
            <TextField label="Description" value={description} onChange={(e) => setDescription(e.target.value)} multiline rows={2} fullWidth />
            <TextField label="Pickup location" value={location} onChange={(e) => setLocation(e.target.value)} fullWidth />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handlePost} disabled={!itemName.trim()}>Post</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
