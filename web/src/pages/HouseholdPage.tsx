import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Button, TextField, Chip,
  Snackbar, Alert, Divider, Stack, Dialog, DialogTitle,
  DialogContent, DialogContentText, DialogActions,
} from "@mui/material";
import { getHousehold, createHousehold, joinHousehold, leaveHousehold } from "../api";

export default function HouseholdPage() {
  const [household, setHousehold] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [createName, setCreateName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [snackbar, setSnackbar] = useState("");
  const [confirmLeave, setConfirmLeave] = useState(false);

  const loadHousehold = useCallback(async () => {
    try {
      const data = await getHousehold();
      setHousehold(data.household ?? data);
    } catch {
      setHousehold(null);
    }
  }, []);

  useEffect(() => { loadHousehold(); }, [loadHousehold]);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    setLoading(true);
    try {
      const data = await createHousehold(createName.trim());
      setHousehold(data);
      setSnackbar(`Created! Share code: ${data.code}`);
      setCreateName("");
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!joinCode.trim()) return;
    setLoading(true);
    try {
      const data = await joinHousehold(joinCode.trim().toUpperCase());
      setHousehold(data);
      setSnackbar(`Joined ${data.name}!`);
      setJoinCode("");
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLeave = async () => {
    await leaveHousehold();
    setHousehold(null);
    setConfirmLeave(false);
    setSnackbar("Left household");
  };

  const hasHousehold = household && household.id;

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Household</Typography>

      {hasHousehold ? (
        <Card>
          <CardContent>
            <Typography variant="h5" fontWeight={800} color="primary">{household.name}</Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" fontWeight={700}>Share Code</Typography>
            <Typography variant="h3" fontWeight={800} sx={{ letterSpacing: 4, textAlign: "center", my: 1 }}>
              {household.code}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Share this code with family members so they can join and see the same pantry.
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
              Members ({household.members?.length || 0})
            </Typography>
            <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap sx={{ mb: 2 }}>
              {household.members?.map((member: string, i: number) => (
                <Chip key={i} label={member} />
              ))}
            </Stack>
            <Button variant="outlined" color="error" onClick={() => setConfirmLeave(true)}>
              Leave Household
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Stack spacing={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Create a Household</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Start a new household and get a code to share with family.
              </Typography>
              <Stack direction="row" spacing={1}>
                <TextField
                  label="Household name"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  sx={{ flex: 1 }}
                />
                <Button variant="contained" onClick={handleCreate} disabled={loading || !createName.trim()}>
                  Create
                </Button>
              </Stack>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={700} gutterBottom>Join a Household</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Enter the 6-character code from a family member.
              </Typography>
              <Stack direction="row" spacing={1}>
                <TextField
                  label="Household code"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  inputProps={{ maxLength: 6, style: { letterSpacing: 4, fontWeight: 700 } }}
                  sx={{ flex: 1 }}
                />
                <Button variant="contained" onClick={handleJoin} disabled={loading || joinCode.length < 6}>
                  Join
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}

      <Dialog open={confirmLeave} onClose={() => setConfirmLeave(false)}>
        <DialogTitle>Leave Household</DialogTitle>
        <DialogContent>
          <DialogContentText>Are you sure? You'll need the code to rejoin.</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmLeave(false)}>Cancel</Button>
          <Button onClick={handleLeave} color="error">Leave</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
