const nodemailer = require("nodemailer");
const dotenv = require("dotenv");
const path = require("path");

// Load environment variables from parent directory's .env file
dotenv.config({ path: path.join(__dirname, "..", ".env") });

// Get email data from command line argument
const emailDataJson = process.argv[2];

if (!emailDataJson) {
  console.error("Error: No email data provided");
  process.exit(1);
}

let emailData;
try {
  emailData = JSON.parse(emailDataJson);
} catch (error) {
  console.error("Error: Invalid JSON data");
  process.exit(1);
}

// Function to create transporter (with Ethereal fallback for testing)
async function createTransporter() {
  // Check if real SMTP credentials are configured
  if (process.env.SMTP_EMAIL && process.env.SMTP_PASSWORD) {
    console.log("[INFO] Using configured SMTP credentials");
    return nodemailer.createTransport({
      host: process.env.SMTP_SERVER || "smtp.gmail.com",
      port: parseInt(process.env.SMTP_PORT) || 587,
      secure: false,
      auth: {
        user: process.env.SMTP_EMAIL,
        pass: process.env.SMTP_PASSWORD,
      },
    });
  } else {
    // Use Ethereal Email for testing (free fake SMTP)
    console.log(
      "[INFO] No SMTP credentials found, using Ethereal Email (test mode)"
    );
    const testAccount = await nodemailer.createTestAccount();
    return nodemailer.createTransport({
      host: "smtp.ethereal.email",
      port: 587,
      secure: false,
      auth: {
        user: testAccount.user,
        pass: testAccount.pass,
      },
    });
  }
}

// Email templates
function getDayStartTemplate(day) {
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:5173';
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Cormorant Garamond', Georgia, serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding: 30px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; border: 2px solid #8B0000; border-radius: 10px; max-width: 600px;">
              <!-- Header -->
              <tr>
                <td style="padding: 30px; text-align: center;">
                  <h1 style="color: #FFD700; font-size: 36px; margin: 0 0 10px 0; font-family: 'Cinzel Decorative', Georgia, serif; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);">
                    🌅 The Godfather
                  </h1>
                  <h2 style="color: #D4AF37; font-size: 24px; margin: 0; font-weight: normal;">
                    Office Mafia Game
                  </h2>
                </td>
              </tr>

              <!-- Main Content -->
              <tr>
                <td style="padding: 0 30px 20px 30px;">
                  <div style="background-color: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #FFD700; font-size: 32px; margin: 0 0 15px 0; text-align: center;">
                      🎮 Day ${day} Has Begun!
                    </h3>
                    <p style="color: #D4AF37; font-size: 18px; line-height: 1.6; text-align: center; margin: 0;">
                      A new day of challenges and opportunities awaits!
                    </p>
                  </div>

                  <div style="background-color: #8B0000; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="color: #FFD700; font-size: 16px; margin: 0; line-height: 1.8;">
                      📋 Check your missions for today<br/>
                      👥 Coordinate with your don family (if related)<br/>
                      🎯 Complete objectives to earn Mafia Dollars (MD)<br/>
                      🏆 Climb the leaderboard!
                    </p>
                  </div>

                  <!-- CTA Button -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                    <tr>
                      <td align="center">
                        <a href="${frontendUrl}" style="background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%); color: #FFD700; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold; display: inline-block;">
                          🎮 Start Playing
                        </a>
                      </td>
                    </tr>
                  </table>

                  <p style="color: #D4AF37; font-size: 14px; text-align: center; margin: 30px 0 0 0; opacity: 0.8;">
                    Good luck, and may the best player prosper! 💼
                  </p>

                  <p style="color: #D4AF37; font-size: 12px; text-align: center; margin: 30px 0 0 0; opacity: 0.8;">
                    *** Note: This is an automated reminder email, if got any problem contact GodFather. ***
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
  `;
}

function getMissionUnlockTemplate(day, unlockHour) {
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:5173';
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Cormorant Garamond', Georgia, serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding: 30px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; border: 2px solid #8B0000; border-radius: 10px; max-width: 600px;">
              <!-- Header -->
              <tr>
                <td style="padding: 30px; text-align: center;">
                  <h1 style="color: #FFD700; font-size: 36px; margin: 0 0 10px 0; font-family: 'Cinzel Decorative', Georgia, serif; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);">
                    🎯 The Godfather
                  </h1>
                  <h2 style="color: #D4AF37; font-size: 24px; margin: 0; font-weight: normal;">
                    Office Mafia Game
                  </h2>
                </td>
              </tr>

              <!-- Main Content -->
              <tr>
                <td style="padding: 0 30px 20px 30px;">
                  <div style="background-color: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #FFD700; font-size: 28px; margin: 0 0 15px 0;">
                      ⏰ Day ${day} Missions Unlocking Soon!
                    </h3>
                    <p style="color: #D4AF37; font-size: 18px; line-height: 1.6; margin: 0;">
                      The missions for <strong>Day ${day}</strong> will unlock at <strong>${unlockHour}:00</strong>!
                    </p>
                  </div>

                  <div style="background-color: #8B0000; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="color: #FFD700; font-size: 16px; margin: 0; line-height: 1.8;">
                      💰 Complete missions to earn Mafia Dollar (MD) and items<br/>
                      🏆 Compete with and without your family for glory<br/>
                      🎯 Don't miss out on today's opportunities!
                    </p>
                  </div>

                  <!-- CTA Button -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                    <tr>
                      <td align="center">
                        <a href="${frontendUrl}/missions" style="background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%); color: #FFD700; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold; display: inline-block;">
                          🎮 View Missions
                        </a>
                      </td>
                    </tr>
                  </table>

                  <p style="color: #D4AF37; font-size: 14px; text-align: center; margin: 30px 0 0 0; opacity: 0.8;">
                    May the best player win! 🏆
                  </p>

                  <p style="color: #D4AF37; font-size: 12px; text-align: center; margin: 30px 0 0 0; opacity: 0.8;">
                    *** Note: This is an automated reminder email, if got any problem contact GodFather. ***
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
  `;
}

function getBlackMarketTemplate(openTime, itemsCount) {
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:5173';
  const itemsText =
    itemsCount > 0 ? `${itemsCount} new items` : "exclusive items";

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Cormorant Garamond', Georgia, serif; background-color: #0a0a0a;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 30px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; border: 2px solid #8B0000; border-radius: 10px; max-width: 600px;">
              <!-- Header -->
              <tr>
                <td style="padding: 30px; text-align: center;">
                  <h1 style="color: #FFD700; font-size: 36px; margin: 0 0 10px 0; font-family: 'Cinzel Decorative', Georgia, serif; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);">
                    🏪 The Godfather
                  </h1>
                  <h2 style="color: #D4AF37; font-size: 24px; margin: 0; font-weight: normal;">
                    Office Mafia Game
                  </h2>
                </td>
              </tr>

              <!-- Main Content -->
              <tr>
                <td style="padding: 0 30px 20px 30px;">
                  <div style="background-color: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #FFD700; font-size: 28px; margin: 0 0 15px 0;">
                      ⚠️ Black Market Opening Soon!
                    </h3>
                    <p style="color: #D4AF37; font-size: 18px; line-height: 1.6; margin: 0;">
                      The <strong>Black Market</strong> opens at <strong>${openTime}</strong> - that's in just <strong style="color: #DC143C;">5 minutes</strong>!
                    </p>
                  </div>

                  <div style="background-color: #8B0000; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="color: #FFD700; font-size: 16px; margin: 0; line-height: 1.8;">
                      💎 ${itemsText} available<br/>
                      💰 Spend your hard-earned money<br/>
                      🔫 Get weapons, items, and advantages<br/>
                      ⏰ Limited time - first come, first served!
                    </p>
                  </div>

                  <!-- CTA Button -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                    <tr>
                      <td align="center">
                        <a href="${frontendUrl}/trade" style="background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%); color: #FFD700; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold; display: inline-block;">
                          🛒 Visit Black Market
                        </a>
                      </td>
                    </tr>
                  </table>

                  <p style="color: #D4AF37; font-size: 14px; text-align: center; margin: 30px 0 0 0; opacity: 0.8;">
                    Don't miss out! Get there early! 🏃‍♂️💨
                  </p>

                  <p style="color: #D4AF37; font-size: 12px; text-align: center; margin: 30px 0 0 0; opacity: 0.8;">
                    *** Note: This is an automated reminder email, if got any problem contact GodFather. ***
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
  `;
}

// Generate email content based on type
function getEmailContent(emailData) {
  const { type, day, unlock_hour, open_time, items_count } = emailData;

  switch (type) {
    case "day_start":
      return {
        subject: `🌅 Day ${day} Has Started! - The Godfather: Office Mafia`,
        html: getDayStartTemplate(day),
      };

    case "mission_unlock":
      return {
        subject: `🎯 Day ${day} Missions Unlocking Soon! - The Godfather`,
        html: getMissionUnlockTemplate(day, unlock_hour),
      };

    case "blackmarket":
      return {
        subject: `🏪 Black Market Opening in 5 Minutes! - The Godfather`,
        html: getBlackMarketTemplate(open_time, items_count || 0),
      };

    default:
      throw new Error(`Unknown email type: ${type}`);
  }
}

// Send email
async function sendEmail() {
  try {
    // Create transporter (either real SMTP or Ethereal test)
    const transporter = await createTransporter();

    const { recipients } = emailData;
    const { subject, html } = getEmailContent(emailData);

    const mailOptions = {
      from: `"The Godfather Game" <noreply@godfather.game>`,
      to: recipients.join(", "),
      subject: subject,
      html: html,
    };

    console.log(
      `Sending ${emailData.type} email to ${recipients.length} recipient(s)...`
    );

    const info = await transporter.sendMail(mailOptions);

    console.log("[SUCCESS] Email sent successfully!");
    console.log("Message ID:", info.messageId);
    console.log(`Recipients: ${recipients.join(", ")}`);

    // If using Ethereal, show preview URL
    const previewUrl = nodemailer.getTestMessageUrl(info);
    if (previewUrl) {
      console.log("[INFO] This is a TEST email (not actually sent)");
      console.log("[INFO] Preview URL:", previewUrl);
      console.log(
        "[INFO] To send real emails, add SMTP credentials to backend/.env"
      );
    }

    process.exit(0);
  } catch (error) {
    console.error("[ERROR] Error sending email:", error.message);
    process.exit(1);
  }
}

// Run
sendEmail();
